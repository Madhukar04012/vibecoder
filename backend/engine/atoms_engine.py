"""
Atoms Engine orchestrator (web execution path).

This module now delegates orchestration to the unified core PipelineRunner so
CLI and web generation share one deterministic execution engine.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from backend.core.pipeline_runner import (
    PipelineContext,
    PipelineRequest,
    run_pipeline as run_unified_pipeline,
)
from backend.engine.events import EngineEventType, get_event_emitter
from backend.engine.state import EngineState, EngineStateMachine
from backend.engine.token_ledger import ledger
from backend.memory.indexer import clear_index
from backend.storage.artifact_store import flatten_structure, get_artifact_store


MERMAID_PATTERN = re.compile(
    r"(graph\s+(TD|TB|BT|RL|LR)|sequenceDiagram|classDiagram|stateDiagram|erDiagram|flowchart)",
    re.IGNORECASE,
)


class AtomsEngine:
    """Web-facing orchestration facade around the unified PipelineRunner."""

    def __init__(
        self,
        run_id: Optional[str] = None,
        project_id: Optional[str] = None,
        user_id: str = "atoms-web",
        token_tier: str = "free",
    ):
        self.run_id = run_id
        self.project_id = project_id
        self.user_id = user_id
        self.token_tier = token_tier

        self.state_machine = EngineStateMachine()
        self.events = get_event_emitter()

        self.prd: Optional[Dict[str, Any]] = None
        self.roadmap: Optional[Dict[str, Any]] = None
        self.files: Dict[str, str] = {}
        self.validation: Dict[str, Any] = {}
        self.qa_result: Optional[Dict[str, Any]] = None
        self.qa_passed: bool = False

        self.diagram_acknowledged = False
        self.has_diagram = False
        self.diagram_path: Optional[str] = None

        self._last_result: Dict[str, Any] | None = None

    @property
    def state(self) -> EngineState:
        return self.state_machine.state

    def run(self, user_prompt: str) -> Dict[str, Any]:
        """Execute the unified pipeline and return Atoms-compatible payload."""

        def _forward_event(name: str, payload: Dict[str, Any]) -> None:
            self._bridge_runner_event(name, payload)

        request = PipelineRequest(
            idea=user_prompt,
            mode="full",
            run_id=self.run_id,
            channel="web",
            user_id=self.user_id,
            project_id=self.project_id,
            token_tier=self.token_tier,
            memory_scope="project",
        )

        result = run_unified_pipeline(request, PipelineContext(on_event=_forward_event, strict_contracts=True))
        self._last_result = result

        self._sync_state_machine(result.get("state_history", []))
        self.prd = result.get("agent_outputs", {}).get("planner")
        self.roadmap = result.get("execution_plan")
        self.qa_result = result.get("agent_outputs", {}).get("tester")
        self.qa_passed = isinstance(self.qa_result, dict) and self.qa_result.get("status") == "success"
        self.validation = {
            "contracts_enforced": True,
            "partial_failures": result.get("partial_failures", []),
        }

        self.files = self._load_generated_files(result)
        self._check_for_mermaid_diagram()

        return {
            "success": bool(result.get("success")),
            "error": result.get("error"),
            "blocked": result.get("state") in {EngineState.FAILED.value, EngineState.TIMEOUT.value, EngineState.CANCELLED.value},
            "state": result.get("state"),
            "prd": self.prd,
            "roadmap": self.roadmap,
            "files": self.files,
            "file_count": len(self.files),
            "validation": self.validation,
            "qa_result": self.qa_result,
            "qa_passed": self.qa_passed,
            "cost": {
                "total_usd": result.get("cost", {}).get("total_usd", 0.0),
                "total_cost_usd": result.get("cost", {}).get("total_usd", 0.0),
                "total_tokens": result.get("cost", {}).get("total_tokens", 0),
                "breakdown": result.get("cost", {}).get("breakdown", {}),
            },
            "run_id": result.get("run_id"),
            "pipeline_result": result,
        }

    def get_cost_summary(self) -> Dict[str, Any]:
        return ledger.get_summary()

    def reset(self) -> None:
        self.state_machine.reset()
        self.prd = None
        self.roadmap = None
        self.files = {}
        self.validation = {}
        self.qa_result = None
        self.qa_passed = False
        self.diagram_acknowledged = False
        self.has_diagram = False
        self.diagram_path = None
        self._last_result = None
        clear_index()
        ledger.reset()

    def acknowledge_diagram(self) -> bool:
        if not self.has_diagram:
            return False
        self.diagram_acknowledged = True
        self.events.emit(
            EngineEventType.DIAGRAM_ACKNOWLEDGED,
            {"diagram_path": self.diagram_path},
            run_id=self.run_id,
        )
        return True

    def _bridge_runner_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        mapped = {
            "state_transition": EngineEventType.AGENT_STATUS,
            "agent_started": EngineEventType.AGENT_STARTED,
            "agent_completed": EngineEventType.AGENT_COMPLETED,
            "agent_failed": EngineEventType.ERROR,
            "agent_retry": EngineEventType.WARNING,
            "run_started": EngineEventType.PLANNING_STARTED,
            "run_finished": EngineEventType.EXECUTION_COMPLETED,
            "run_failed": EngineEventType.EXECUTION_FAILED,
        }
        event_type = mapped.get(event_name, EngineEventType.AGENT_STATUS)
        payload_with_event = {"event": event_name, **payload}
        self.events.emit(event_type, payload_with_event, run_id=self.run_id)

    def _sync_state_machine(self, history: list[str]) -> None:
        self.state_machine.reset()
        if not history:
            return

        for state_name in history[1:]:
            try:
                state = EngineState(state_name)
            except Exception:
                continue
            if state in self.state_machine.history:
                continue
            try:
                self.state_machine.transition(state)
            except Exception:
                # Keep best-effort state reconstruction only.
                break

    def _load_generated_files(self, result: Dict[str, Any]) -> Dict[str, str]:
        manifest = result.get("artifact_manifest")
        if not manifest:
            coder_output = result.get("agent_outputs", {}).get("coder", {})
            if isinstance(coder_output, dict):
                return flatten_structure(coder_output)
            return {}

        project_key = manifest.get("project_key")
        version = int(manifest.get("version", 0))
        if not project_key or version <= 0:
            return {}

        try:
            return get_artifact_store().load_version(project_key=project_key, version=version)
        except Exception:
            return {}

    def _check_for_mermaid_diagram(self) -> None:
        if not self.roadmap:
            return

        roadmap_str = json.dumps(self.roadmap)
        if MERMAID_PATTERN.search(roadmap_str):
            self.has_diagram = True
            self.diagram_path = None
            self.events.emit(
                EngineEventType.PLANNING_DIAGRAM_UPDATED,
                {"content_preview": roadmap_str[:500]},
                run_id=self.run_id,
            )


# Convenience wrappers

def run_pipeline(prompt: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    engine = AtomsEngine(run_id=run_id)
    return engine.run(prompt)


def get_current_cost() -> Dict[str, Any]:
    return ledger.get_summary()
