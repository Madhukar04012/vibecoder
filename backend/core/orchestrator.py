"""
Orchestrator facade.

`orchestrate()` now delegates to the unified PipelineRunner for both CLI and API paths.
Legacy v1 flow is retained for backward compatibility.
"""

from __future__ import annotations

from typing import Any, Dict

from backend.agents.coder import code_agent
from backend.agents.planner import planner_agent
from backend.core.pipeline_runner import PipelineRequest, run_pipeline


def run_agents_v2(user_idea: str, mode: str = "full") -> Dict[str, Any]:
    """Run the unified contract-enforced pipeline."""
    request = PipelineRequest(
        idea=user_idea,
        mode=mode,
        channel="cli",
        user_id="local-cli",
        memory_scope="project",
    )
    return run_pipeline(request)


def run_agents(user_idea: str) -> Dict[str, Any]:
    """Legacy Phase-1 flow (planner -> coder)."""
    architecture = planner_agent(user_idea)
    project_structure = code_agent(architecture, user_idea=user_idea)
    return {
        "input_idea": user_idea,
        "architecture": architecture,
        "project_structure": project_structure,
    }


def orchestrate(user_idea: str, mode: str = "full", use_v2: bool = True) -> Dict[str, Any]:
    """Main orchestration entry point."""
    if use_v2:
        return run_agents_v2(user_idea, mode=mode)
    return run_agents(user_idea)
