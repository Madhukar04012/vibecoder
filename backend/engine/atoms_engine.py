"""
Atoms Engine Orchestrator — Phase-1 + Phase-2 Events + Phase-3 QA

The central brain that controls agent execution.
Agents are workers, the engine is the boss.

This class integrates:
- State machine for phase gating
- Token ledger for cost tracking
- Planning validation before execution
- Semantic memory for context retrieval
- Event system for UI integration (Phase-2)
- Diagram acknowledgment gate (Phase-2)
- QA Agent with circuit breaker (Phase-3)

Usage:
    engine = AtomsEngine()
    result = engine.run("Build a todo app")
    
    print(result["cost"])  # Total cost in USD
    print(result["qa_result"])  # QA test results
"""

from typing import Optional, Dict, Any, List, Callable
import json
import re

from backend.engine.state import EngineStateMachine, EngineState, EngineStateError
from backend.engine.events import EventEmitter, EngineEventType, get_event_emitter
from backend.engine.token_ledger import ledger, BudgetExceededError
from backend.engine.planning_validator import validate_planning_output, get_validation_summary
from backend.agents.product_manager import ProductManagerAgent
from backend.agents.architect import ArchitectAgent
from backend.agents.engineer import EngineerAgent
from backend.memory.indexer import index_file, clear_index
from backend.memory.retriever import has_indexed_content


# Mermaid diagram detection pattern
MERMAID_PATTERN = re.compile(r'(graph\s+(TD|TB|BT|RL|LR)|sequenceDiagram|classDiagram|stateDiagram|erDiagram|flowchart)', re.IGNORECASE)


class AtomsEngine:
    """
    The orchestrator for the multi-agent pipeline.
    
    Enforces:
    - State machine transitions
    - Planning before execution
    - Cost tracking per agent
    - Semantic memory context
    - Event emission for UI (Phase-2)
    - Diagram acknowledgment gate (Phase-2)
    """
    
    def __init__(self, run_id: Optional[str] = None):
        """
        Initialize the engine.
        
        Args:
            run_id: Optional run identifier for tracking
        """
        self.state_machine = EngineStateMachine()
        self.run_id = run_id
        
        # Planning outputs
        self.prd: Optional[Dict[str, Any]] = None
        self.roadmap: Optional[Dict[str, Any]] = None
        
        # Generated files
        self.files: Dict[str, str] = {}
        
        # Validation results
        self.validation: Dict[str, Any] = {}
        
        # Phase-2: Event system
        self.events = get_event_emitter()
        
        # Phase-2: Diagram acknowledgment gate
        self.diagram_acknowledged = False
        self.has_diagram = False
        self.diagram_path: Optional[str] = None
        
        # Phase-3: QA results
        self.qa_result: Optional[Dict[str, Any]] = None
        self.qa_passed = False
        
        # Start fresh ledger
        ledger.start_run(run_id)
    
    @property
    def state(self) -> EngineState:
        """Current engine state."""
        return self.state_machine.state
    
    def run(self, user_prompt: str) -> Dict[str, Any]:
        """
        Execute the full pipeline: Planning → Approval → Execution.
        
        Args:
            user_prompt: User's project description
            
        Returns:
            Result dict with files, cost, validation info
        """
        try:
            # 1. Planning Phase
            self._run_planning(user_prompt)
            
            # 2. Automatic Approval (in Phase-1, no user gate)
            self.state_machine.transition(EngineState.APPROVED)
            
            # 3. Execution Phase
            self._run_execution()
            
            # 4. Phase-3: QA Testing
            qa_result = self._run_qa()
            
            if qa_result["status"] == "escalated":
                # Circuit breaker triggered — block deployment
                self.state_machine.transition(EngineState.IDLE)
                return self._build_result(
                    success=False,
                    error="QA Circuit Breaker: Repeated test failures",
                    blocked=True
                )
            
            # 5. Complete
            self.state_machine.transition(EngineState.IDLE)
            
            return self._build_result(success=True)
            
        except BudgetExceededError as e:
            # Budget breached — pause and escalate to human
            self.state_machine.transition(EngineState.AWAITING_HUMAN)
            self.emit_event(EngineEventType.WARNING, {
                "source": "budget_enforcement",
                "message": str(e),
                "budget": e.budget,
                "current_cost": e.current_cost,
                "attempted_cost": e.attempted_cost,
            })
            return self._build_result(
                success=False,
                error=f"Budget exceeded: {e}",
                blocked=True,
            )
        except EngineStateError as e:
            return self._build_result(success=False, error=f"State error: {e}")
        except ValueError as e:
            return self._build_result(success=False, error=f"Validation error: {e}")
        except Exception as e:
            return self._build_result(success=False, error=f"Execution error: {e}")
    
    def _run_planning(self, user_prompt: str) -> None:
        """Execute the planning phase (PM + Architect)."""
        self.state_machine.transition(EngineState.PLANNING)
        self.emit_event(EngineEventType.PLANNING_STARTED, {"prompt": user_prompt[:200]})
        
        # 1. Product Manager generates PRD
        pm = ProductManagerAgent()
        self.state_machine.validate_agent(pm.name)
        self.emit_event(EngineEventType.AGENT_STARTED, {"agent": pm.name, "task": "Generating PRD"})
        self.prd = pm.generate_prd(user_prompt)
        self.emit_event(EngineEventType.AGENT_COMPLETED, {"agent": pm.name})
        
        # 2. Architect generates roadmap
        architect = ArchitectAgent()
        self.state_machine.validate_agent(architect.name)
        self.emit_event(EngineEventType.AGENT_STARTED, {"agent": architect.name, "task": "Drawing architecture diagram"})
        self.roadmap = architect.generate_roadmap(self.prd)
        self.emit_event(EngineEventType.AGENT_COMPLETED, {"agent": architect.name})
        
        # 3. Check for Mermaid diagram in roadmap
        self._check_for_mermaid_diagram()
        
        # 4. Validate planning outputs
        self.validation = get_validation_summary(self.prd, self.roadmap)
        
        # 5. Hard validation (will raise if critical sections missing)
        validate_planning_output(self.prd, self.roadmap)
        
        self.emit_event(EngineEventType.PLANNING_COMPLETED, {
            "has_diagram": self.has_diagram,
            "validation": self.validation,
        })
    
    def _run_execution(self) -> None:
        """Execute the coding phase (Engineer)."""
        # Phase-2: Check diagram acknowledgment gate
        if self.has_diagram and not self.diagram_acknowledged:
            raise EngineStateError(
                "Diagram must be acknowledged before execution. "
                "Call acknowledge_diagram() or POST /engine/acknowledge-diagram"
            )
        
        self.state_machine.transition(EngineState.EXECUTION)
        self.emit_event(EngineEventType.EXECUTION_STARTED, {})
        
        # Index any existing files for context
        if self.files:
            for path, content in self.files.items():
                index_file(path, content)
        
        # Engineer generates files
        engineer = EngineerAgent(self.prd, self.roadmap)
        self.state_machine.validate_agent(engineer.name)
        self.emit_event(EngineEventType.AGENT_STARTED, {"agent": engineer.name, "task": "Generating code files"})
        
        file_plan = self.roadmap.get("directory_structure", [])
        
        for file_path in file_plan:
            self.emit_event(EngineEventType.AGENT_STATUS, {
                "agent": engineer.name,
                "status": f"Generating {file_path}",
            })
            
            # Use memory-aware generation if we have context
            if has_indexed_content():
                content = engineer.generate_file_with_memory(file_path)
            else:
                content = engineer.generate_file(file_path)
            
            self.files[file_path] = content
            
            # Index generated file for future context
            index_file(file_path, content)
            
            # Emit file change event
            self.emit_event(EngineEventType.FILE_CHANGE_PROPOSED, {
                "path": file_path,
                "content_length": len(content),
            })
        
        self.emit_event(EngineEventType.AGENT_COMPLETED, {"agent": engineer.name})
        self.emit_event(EngineEventType.EXECUTION_COMPLETED, {"file_count": len(self.files)})
    
    def _run_qa(self) -> Dict[str, Any]:
        """
        Execute QA testing phase (Phase-3).
        
        Returns:
            {"status": "passed" | "retry" | "escalated"}
        """
        from backend.agents.qa_tester import QATesterAgent
        
        self.emit_event(EngineEventType.AGENT_STATUS, {
            "agent": "qa_tester",
            "event": "QA_STARTED",
        })
        
        # Create QA agent with PRD and project path
        # For now, pass files directly since we don't have a physical project path yet
        qa = QATesterAgent(prd=self.prd, project_path="")
        
        # QA loop with circuit breaker (engine-controlled)
        while True:
            qa_result = qa.run()
            self.qa_result = qa_result
            
            if qa_result["status"] == "passed":
                self.qa_passed = True
                self.emit_event(EngineEventType.AGENT_STATUS, {
                    "agent": "qa_tester",
                    "event": "QA_PASSED",
                })
                return qa_result
            
            if qa_result["status"] == "escalated":
                # Circuit breaker triggered
                self.emit_event(EngineEventType.ERROR, {
                    "agent": "qa_tester",
                    "event": "CIRCUIT_BREAKER_TRIGGERED",
                    "reason": "Repeated test failures",
                    "errors": qa_result.get("errors", [])[:5],
                })
                return qa_result
            
            # Retry (status == "retry")
            self.emit_event(EngineEventType.AGENT_STATUS, {
                "agent": "qa_tester",
                "event": "QA_RETRY",
                "attempt": qa_result.get("attempt", 0),
            })
    
    def _build_result(self, success: bool, error: Optional[str] = None, blocked: bool = False) -> Dict[str, Any]:
        """Build the final result dict."""
        return {
            "success": success,
            "error": error,
            "blocked": blocked,  # Phase-3: deployment blocked by QA
            "state": self.state.value,
            "prd": self.prd,
            "roadmap": self.roadmap,
            "files": self.files,
            "file_count": len(self.files),
            "validation": self.validation,
            "qa_result": self.qa_result,  # Phase-3: QA test results
            "qa_passed": self.qa_passed,  # Phase-3: QA gate status
            "cost": {
                "total_usd": round(ledger.total_cost, 6),
                "total_tokens": ledger.total_tokens,
                "breakdown": ledger.by_agent,
            },
            "run_id": self.run_id,
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get current cost summary."""
        return ledger.get_summary()
    
    def reset(self) -> None:
        """Reset engine for a new run."""
        self.state_machine.reset()
        self.prd = None
        self.roadmap = None
        self.files = {}
        self.validation = {}
        # Phase-2: Reset diagram state
        self.diagram_acknowledged = False
        self.has_diagram = False
        self.diagram_path = None
        # Phase-3: Reset QA state
        self.qa_result = None
        self.qa_passed = False
        clear_index()
        ledger.reset()
    
    # ─── Phase-2 Methods ─────────────────────────────────────────────────────
    
    def emit_event(self, event_type: EngineEventType, payload: Dict[str, Any]) -> None:
        """
        Emit an engine event.
        
        Args:
            event_type: Type of event
            payload: Event data
        """
        self.events.emit(event_type, payload, run_id=self.run_id)
    
    def acknowledge_diagram(self) -> bool:
        """
        Acknowledge the planning diagram.
        Must be called before execution can proceed.
        
        Returns:
            True if diagram was acknowledged, False if no diagram exists
        """
        if not self.has_diagram:
            return False
        
        self.diagram_acknowledged = True
        self.emit_event(EngineEventType.DIAGRAM_ACKNOWLEDGED, {
            "diagram_path": self.diagram_path,
        })
        return True
    
    def _check_for_mermaid_diagram(self) -> None:
        """
        Check if roadmap contains a Mermaid diagram.
        If found, save it and emit an event.
        """
        if not self.roadmap:
            return
        
        # Convert roadmap to string for pattern matching
        roadmap_str = json.dumps(self.roadmap)
        
        if MERMAID_PATTERN.search(roadmap_str):
            self.has_diagram = True
            
            # Extract diagram content (simplified - looks for common patterns)
            diagram_content = self._extract_mermaid_diagram(roadmap_str)
            
            if diagram_content:
                # Save diagram to file
                self.diagram_path = "roadmap.mmd"
                try:
                    with open(self.diagram_path, "w", encoding="utf-8") as f:
                        f.write(diagram_content)
                except Exception:
                    pass  # Non-critical if save fails
                
                # Emit event
                self.emit_event(EngineEventType.PLANNING_DIAGRAM_UPDATED, {
                    "path": self.diagram_path,
                    "content": diagram_content[:500],  # Preview
                })
    
    def _extract_mermaid_diagram(self, content: str) -> Optional[str]:
        """
        Extract Mermaid diagram from content.
        Looks for common diagram start patterns.
        """
        import re
        
        # Look for fenced code blocks with mermaid
        mermaid_block = re.search(r'```mermaid\s*([\s\S]*?)```', content, re.IGNORECASE)
        if mermaid_block:
            return mermaid_block.group(1).strip()
        
        # Look for raw diagram syntax
        graph_match = re.search(r'(graph\s+(?:TD|TB|BT|RL|LR)[\s\S]*?)(?:\n\n|$)', content)
        if graph_match:
            return graph_match.group(1).strip()
        
        sequence_match = re.search(r'(sequenceDiagram[\s\S]*?)(?:\n\n|$)', content)
        if sequence_match:
            return sequence_match.group(1).strip()
        
        return None


# ─── Convenience Functions ───────────────────────────────────────────────────

def run_pipeline(prompt: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full pipeline with a single function call.
    
    Args:
        prompt: User's project description
        run_id: Optional run identifier
        
    Returns:
        Result dict
    """
    engine = AtomsEngine(run_id)
    return engine.run(prompt)


def get_current_cost() -> Dict[str, Any]:
    """Get cost from the current/last run."""
    return ledger.get_summary()
