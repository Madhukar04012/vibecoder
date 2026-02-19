"""
QA Tester Agent — Phase 3

Agentic QA gatekeeper. Generates tests from PRD, runs in sandbox, decides PASS/FAIL/ESCALATE.

Role Definition (Non-Negotiable):
- QA Agent is NOT a coder
- It only: generates tests, runs tests, decides outcome
- It never: fixes code, rewrites logic, deploys anything

Circuit Breaker:
- MAX_FAILURES = 3
- After 3 failures: ESCALATE, block deployment, return to user

Usage:
    qa = QATesterAgent(prd=prd_dict, project_path="/path/to/project")
    result = qa.run()  # returns {"status": "passed" | "retry" | "escalated"}
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
import os

from backend.agents.base_agent import BaseAgent
from backend.engine.events import get_event_emitter, EngineEventType


# ─── Constants ───────────────────────────────────────────────────────────────

MAX_FAILURES = 3  # Circuit breaker threshold


# ─── QA Result Types ─────────────────────────────────────────────────────────

@dataclass
class QAResult:
    """Result from a QA test run."""
    status: str  # "passed" | "retry" | "escalated"
    passed: bool
    stdout: str = ""
    stderr: str = ""
    errors: List[str] = None
    attempt: int = 0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "errors": self.errors,
            "attempt": self.attempt,
        }


# ─── QA Tester Agent ─────────────────────────────────────────────────────────

class QATesterAgent(BaseAgent):
    """
    QA Agent — Tests code against PRD requirements.
    
    Inherits from BaseAgent to route all LLM calls through the gateway
    for proper cost tracking and budget enforcement.
    
    Responsibilities:
    1. Generate tests from PRD + code context
    2. Run tests in isolated sandbox
    3. Decide PASS / FAIL / ESCALATE
    
    Non-Responsibilities:
    - Does NOT fix code
    - Does NOT rewrite logic
    - Does NOT deploy
    """
    
    name = "qa_tester"
    
    def __init__(self, prd: Dict[str, Any], project_path: str):
        """
        Initialize QA Tester.
        
        Args:
            prd: Product Requirements Document
            project_path: Path to project under test
        """
        super().__init__()
        self.prd = prd
        self.project_path = project_path
        self.failure_count = 0
        self.events = get_event_emitter()
        self._test_history: List[QAResult] = []
    
    def run(self) -> Dict[str, Any]:
        """
        Execute QA testing.
        
        Returns:
            {"status": "passed"} - All tests pass
            {"status": "retry"} - Tests failed, can retry
            {"status": "escalated", "errors": [...]} - Circuit breaker triggered
        """
        self._emit_event(EngineEventType.AGENT_STARTED, {
            "agent": self.name,
            "task": "Running QA tests",
            "attempt": self.failure_count + 1,
        })
        
        # Generate tests from PRD
        test_code = self.generate_tests()
        
        if not test_code:
            self._emit_event(EngineEventType.WARNING, {
                "agent": self.name,
                "message": "Failed to generate tests",
            })
            return self._handle_failure(["Test generation failed"])
        
        # Execute tests in sandbox
        result = self.execute_tests(test_code)
        
        if result.passed:
            self._emit_event(EngineEventType.AGENT_COMPLETED, {
                "agent": self.name,
                "status": "passed",
                "stdout": result.stdout[:500],
            })
            # Emit QA_PASSED event
            self.events.emit(EngineEventType.AGENT_STATUS, {
                "agent": self.name,
                "event": "QA_PASSED",
                "details": result.to_dict(),
            })
            return {"status": "passed"}
        
        # Handle failure
        return self._handle_failure(result.errors)
    
    def _handle_failure(self, errors: List[str]) -> Dict[str, Any]:
        """Handle test failure with circuit breaker logic."""
        self.failure_count += 1
        
        # Emit failure event
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": self.name,
            "event": "QA_FAILED",
            "attempt": self.failure_count,
            "errors": errors[:5],  # Limit error count
        })
        
        # Check circuit breaker
        if self.failure_count >= MAX_FAILURES:
            self._emit_event(EngineEventType.ERROR, {
                "agent": self.name,
                "event": "CIRCUIT_BREAKER_TRIGGERED",
                "reason": "Repeated test failures",
                "attempts": self.failure_count,
                "errors": errors[:5],
            })
            return {
                "status": "escalated",
                "errors": errors,
                "attempts": self.failure_count,
            }
        
        return {"status": "retry", "attempt": self.failure_count}
    
    def generate_tests(self) -> Optional[str]:
        """
        Generate tests from PRD.
        
        Tests are derived from acceptance criteria, not code structure.
        This ensures tests verify requirements, not implementation details.
        """
        # Build prompt from PRD
        prd_text = self._format_prd()
        
        prompt = f"""You are a senior QA engineer.

Given this Product Requirement Document:
{prd_text}

Write minimal but strict unit tests that verify:
- Functional correctness
- Edge cases
- Error handling

Rules:
- Use pytest (Python) or jest (JS) depending on the project
- Do NOT mock core logic
- Tests must fail if requirements are unmet
- Keep tests focused and minimal
- Include setup/teardown if needed

Output ONLY the test code. No explanations."""
        
        try:
            test_code = self._call_llm(prompt)
            
            if not test_code:
                return None
            
            # Clean up markdown fences
            test_code = self._clean_code(test_code)
            
            return test_code
            
        except Exception as e:
            print(f"[QA] Test generation error: {e}")
            return None
    
    def execute_tests(self, test_code: str) -> QAResult:
        """
        Execute tests in isolated sandbox.
        
        Uses testing_service for sandbox isolation.
        """
        from backend.services.testing_service import run_tests
        
        try:
            result = run_tests(self.project_path, test_code)
            
            qa_result = QAResult(
                status="passed" if result["passed"] else "failed",
                passed=result["passed"],
                stdout=result.get("stdout", ""),
                stderr=result.get("stderr", ""),
                errors=result.get("errors", []) if not result["passed"] else [],
                attempt=self.failure_count + 1,
            )
            
            self._test_history.append(qa_result)
            return qa_result
            
        except Exception as e:
            return QAResult(
                status="error",
                passed=False,
                stderr=str(e),
                errors=[str(e)],
                attempt=self.failure_count + 1,
            )
    
    def _format_prd(self) -> str:
        """Format PRD for prompt."""
        if isinstance(self.prd, dict):
            parts = []
            if "title" in self.prd:
                parts.append(f"Title: {self.prd['title']}")
            if "description" in self.prd:
                parts.append(f"Description: {self.prd['description']}")
            if "features" in self.prd:
                parts.append(f"Features: {', '.join(self.prd['features'])}")
            if "user_stories" in self.prd:
                parts.append(f"User Stories:\n" + "\n".join(f"- {s}" for s in self.prd['user_stories']))
            if "constraints" in self.prd:
                parts.append(f"Constraints: {', '.join(self.prd['constraints'])}")
            return "\n\n".join(parts)
        return str(self.prd)
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """Call LLM for test generation via the gateway (cost-tracked)."""
        return self.call_llm_simple(
            system="You are a senior QA engineer. Output only test code.",
            user=prompt,
            max_tokens=2048,
            temperature=0.2,
        )
    
    def _clean_code(self, code: str) -> str:
        """Remove markdown fences from code."""
        import re
        code = re.sub(r'^```\w*\n?', '', code.strip())
        code = re.sub(r'\n?```$', '', code.strip())
        return code
    
    def _emit_event(self, event_type: EngineEventType, payload: Dict[str, Any]) -> None:
        """Emit an engine event."""
        self.events.emit(event_type, payload)
    
    def get_test_history(self) -> List[Dict[str, Any]]:
        """Get history of all test runs."""
        return [r.to_dict() for r in self._test_history]
    
    def reset(self) -> None:
        """Reset failure count and history."""
        self.failure_count = 0
        self._test_history = []
