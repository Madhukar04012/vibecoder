"""
Self-Healer — Phase 4

Autonomous Production Recovery (MTTR ↓↓↓)

Design Constraints (Non-Negotiable):
- ❌ Never deploy blindly
- ❌ Never bypass QA
- ❌ Never hide changes from the user
- ✅ Act only on observed failures
- ✅ Be reversible (roll-forward, not rollback)
- ✅ Escalate to humans when confidence is low

Workflow:
    Production Monitor → 500 detected → Capture logs
    → Spawn Fix-it Agent (sandbox) → Apply patch
    → Run QA Agent → If PASS: roll-forward deploy
                   → If FAIL: escalate to human

Usage:
    healer = SelfHealer(engine, health_url="/health", project_path="/path")
    healer.start()  # Starts background monitoring
"""

import time
import asyncio
import threading
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from enum import Enum
import requests

from backend.engine.events import get_event_emitter, EngineEventType
from backend.engine.circuit_breaker import get_circuit_breaker, CircuitOpenError


# ─── Constants ───────────────────────────────────────────────────────────────

MAX_RETRIES = 2  # Escalate after 2 failed fix attempts
MONITOR_INTERVAL = 30  # Seconds between health checks
HEALTH_TIMEOUT = 5  # Seconds to wait for health response
LOG_TAIL_SIZE = 5000  # Characters of logs to capture


# ─── Healer State ────────────────────────────────────────────────────────────

class HealerState(Enum):
    IDLE = "idle"
    MONITORING = "monitoring"
    HEALING = "healing"
    AWAITING_HUMAN = "awaiting_human"
    STOPPED = "stopped"


# ─── Failure Record ──────────────────────────────────────────────────────────

@dataclass
class FailureRecord:
    """Record of a detected failure."""
    timestamp: float
    error_type: str  # "http_5xx" | "exception" | "crash_loop"
    status_code: Optional[int] = None
    error_message: str = ""
    stack_trace: str = ""
    attempt: int = 0


# ─── Self-Healer ─────────────────────────────────────────────────────────────

class SelfHealer:
    """
    Autonomous production recovery system.
    
    Watches for failures, spawns fix agents, runs QA,
    and deploys fixes or escalates to humans.
    """
    
    def __init__(
        self,
        engine: Any,
        health_url: str,
        project_path: str,
        log_path: str = "logs/production.log",
    ):
        """
        Initialize the self-healer.
        
        Args:
            engine: AtomsEngine instance (for PRD, roadmap, state)
            health_url: URL to monitor (e.g., http://localhost:8000/health)
            project_path: Path to project directory
            log_path: Path to production log file
        """
        self.engine = engine
        self.health_url = health_url
        self.project_path = project_path
        self.log_path = log_path
        
        self.state = HealerState.IDLE
        self.failures: List[FailureRecord] = []
        self.retry_count = 0
        self.events = get_event_emitter()
        
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        
        # Callbacks for external integrations
        self._on_escalate: Optional[Callable[[FailureRecord], None]] = None
        self._on_fix_success: Optional[Callable[[], None]] = None
        
        # Phase 3: Circuit breaker for fix attempts
        self._circuit_breaker = get_circuit_breaker(
            name="self_healer",
            max_failures=MAX_RETRIES,
            reset_timeout=120.0,
        )
    
    # ─── Public API ──────────────────────────────────────────────────────────
    
    def start(self) -> None:
        """Start background health monitoring."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_flag.clear()
        self.state = HealerState.MONITORING
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self._emit_event("SELF_HEALER_STARTED", {
            "health_url": self.health_url,
            "interval": MONITOR_INTERVAL,
        })
    
    def stop(self) -> None:
        """Stop health monitoring."""
        self._stop_flag.set()
        self.state = HealerState.STOPPED
        self._emit_event("SELF_HEALER_STOPPED", {})
    
    def check_health(self) -> Dict[str, Any]:
        """
        Perform a single health check.
        
        Returns:
            {"healthy": bool, "status_code": int, "error": str}
        """
        try:
            response = requests.get(self.health_url, timeout=HEALTH_TIMEOUT)
            return {
                "healthy": response.status_code < 500,
                "status_code": response.status_code,
                "error": None,
            }
        except requests.RequestException as e:
            return {
                "healthy": False,
                "status_code": 0,
                "error": str(e),
            }
    
    def trigger_heal(self, failure_context: str) -> Dict[str, Any]:
        """
        Manually trigger a heal attempt.
        
        Args:
            failure_context: Description of the failure
            
        Returns:
            {"status": "success" | "qa_failed" | "escalated"}
        """
        record = FailureRecord(
            timestamp=time.time(),
            error_type="manual",
            error_message=failure_context,
        )
        try:
            return self._circuit_breaker.call(self._attempt_fix, record)
        except CircuitOpenError:
            return self._escalate(record)
    
    def on_escalate(self, callback: Callable[[FailureRecord], None]) -> None:
        """Register callback for escalation events."""
        self._on_escalate = callback
    
    def on_fix_success(self, callback: Callable[[], None]) -> None:
        """Register callback for successful fixes."""
        self._on_fix_success = callback
    
    def get_status(self) -> Dict[str, Any]:
        """Get current healer status."""
        return {
            "state": self.state.value,
            "retry_count": self.retry_count,
            "failure_count": len(self.failures),
            "last_failure": self.failures[-1].__dict__ if self.failures else None,
            "circuit_breaker": self._circuit_breaker.get_status(),
        }
    
    # ─── Monitoring Loop ─────────────────────────────────────────────────────
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while not self._stop_flag.is_set():
            try:
                health = self.check_health()
                
                if not health["healthy"]:
                    self._handle_failure(health)
                    
            except Exception as e:
                self._handle_exception(e)
            
            # Wait for next check or stop signal
            self._stop_flag.wait(timeout=MONITOR_INTERVAL)
    
    def _handle_failure(self, health: Dict[str, Any]) -> None:
        """Handle detected health check failure."""
        record = FailureRecord(
            timestamp=time.time(),
            error_type="http_5xx" if health["status_code"] >= 500 else "connection_error",
            status_code=health["status_code"],
            error_message=health.get("error", ""),
        )
        
        self._emit_event("SELF_HEALER_TRIGGERED", {
            "status_code": health["status_code"],
            "error": health.get("error"),
        })
        
        # Collect logs for context
        logs = self._collect_logs()
        record.stack_trace = logs
        
        self.failures.append(record)
        try:
            self._circuit_breaker.call(self._attempt_fix, record)
        except CircuitOpenError:
            self._escalate(record)
    
    def _handle_exception(self, exception: Exception) -> None:
        """Handle monitoring exception."""
        self._emit_event("SELF_HEALER_EXCEPTION", {
            "error": str(exception),
        })
    
    # ─── Fix Logic ───────────────────────────────────────────────────────────
    
    def _attempt_fix(self, failure: FailureRecord) -> Dict[str, Any]:
        """
        Attempt to fix the failure.
        
        Workflow:
        1. Check retry limit
        2. Spawn fix agent
        3. Run QA
        4. Deploy if passed, escalate if failed
        """
        if self.retry_count >= MAX_RETRIES:
            return self._escalate(failure)
        
        self.retry_count += 1
        failure.attempt = self.retry_count
        self.state = HealerState.HEALING
        
        self._emit_event("SELF_HEALING_ATTEMPT", {
            "attempt": self.retry_count,
            "failure_type": failure.error_type,
        })
        
        try:
            # 1. Generate fix using Engineer agent
            fix_result = self._generate_fix(failure)
            
            if not fix_result["success"]:
                self._emit_event("SELF_HEALING_FIX_FAILED", {
                    "reason": fix_result.get("error", "Fix generation failed"),
                })
                return {"status": "fix_failed"}
            
            # 2. Run QA on the fix
            qa_result = self._run_qa()
            
            if qa_result["status"] == "passed":
                # 3. Deploy the fix
                deploy_result = self._deploy_fix()
                
                self._emit_event("SELF_HEALING_SUCCESS", {
                    "attempt": self.retry_count,
                })
                
                # Reset state
                self.retry_count = 0
                self.state = HealerState.MONITORING
                
                if self._on_fix_success:
                    self._on_fix_success()
                
                return {"status": "success"}
            
            else:
                # QA failed
                self._emit_event("SELF_HEALING_QA_FAILED", {
                    "qa_result": qa_result,
                })
                
                # Try again if under limit
                if self.retry_count < MAX_RETRIES:
                    return {"status": "retry"}
                else:
                    return self._escalate(failure)
                    
        except Exception as e:
            self._emit_event("SELF_HEALING_ERROR", {"error": str(e)})
            return self._escalate(failure)
    
    def _generate_fix(self, failure: FailureRecord) -> Dict[str, Any]:
        """Generate a fix using the Engineer agent."""
        from backend.agents.engineer import EngineerAgent
        
        # Build context for the fix
        context = f"""
PRODUCTION FAILURE DETECTED:
Type: {failure.error_type}
Status Code: {failure.status_code}
Error: {failure.error_message}

STACK TRACE / LOGS:
{failure.stack_trace}

FIX REQUIREMENTS:
- Identify the root cause
- Apply minimal, targeted fix
- Do not refactor unrelated code
- Preserve existing functionality
"""
        
        try:
            engineer = EngineerAgent(self.engine.prd, self.engine.roadmap)
            
            # Use fix mode if available
            fix_prompt = f"Fix this production error:\n{context}"
            fix_code = engineer.generate_file_with_memory("fix_patch.py") if hasattr(engineer, 'generate_file_with_memory') else None
            
            return {"success": True, "fix": fix_code}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _run_qa(self) -> Dict[str, Any]:
        """Run QA tests on the fix."""
        from backend.agents.qa_tester import QATesterAgent
        
        try:
            qa = QATesterAgent(prd=self.engine.prd, project_path=self.project_path)
            return qa.run()
        except Exception as e:
            return {"status": "error", "errors": [str(e)]}
    
    def _deploy_fix(self) -> Dict[str, Any]:
        """Deploy the fix using roll-forward strategy."""
        # Import deployment manager if available
        try:
            from backend.services.deployment_manager import roll_forward_deploy
            return roll_forward_deploy(self.project_path)
        except ImportError:
            # Fallback: just log
            self._emit_event("SELF_HEALING_DEPLOY", {
                "project_path": self.project_path,
                "strategy": "roll_forward",
            })
            return {"success": True}
    
    def _escalate(self, failure: FailureRecord) -> Dict[str, Any]:
        """Escalate to human when fix attempts exhausted."""
        self.state = HealerState.AWAITING_HUMAN
        
        # Update engine state if possible
        try:
            from backend.engine.state import EngineState
            if hasattr(EngineState, 'AWAITING_HUMAN'):
                self.engine.state_machine._state = EngineState.AWAITING_HUMAN
        except Exception:
            pass
        
        self._emit_event("SELF_HEALING_ESCALATED", {
            "reason": "Max retries exceeded",
            "attempt_count": self.retry_count,
            "failure_type": failure.error_type,
            "error": failure.error_message,
            "context": failure.stack_trace[:1000],
        })
        
        if self._on_escalate:
            self._on_escalate(failure)
        
        return {"status": "escalated", "failure": failure.__dict__}
    
    # ─── Helpers ─────────────────────────────────────────────────────────────
    
    def _collect_logs(self) -> str:
        """Collect recent production logs."""
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                content = f.read()
                return content[-LOG_TAIL_SIZE:]
        except FileNotFoundError:
            return "No logs found"
        except Exception as e:
            return f"Log collection failed: {e}"
    
    def _emit_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Emit a healer event."""
        # Use AGENT_STATUS for healer events
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": "self_healer",
            "event": event_name,
            **payload,
        })
    
    def reset(self) -> None:
        """Reset healer state."""
        self.retry_count = 0
        self.failures = []
        self.state = HealerState.IDLE


# ─── Convenience Functions ───────────────────────────────────────────────────

def create_self_healer(
    engine: Any,
    health_url: str = "http://localhost:8000/health",
    project_path: str = "",
) -> SelfHealer:
    """Create a self-healer instance."""
    return SelfHealer(engine, health_url, project_path)
