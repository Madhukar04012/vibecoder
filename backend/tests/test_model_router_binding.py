from __future__ import annotations

import pytest

from backend.core.llm_client import LLMClient
from backend.core.model_router import ModelRouter, ModelRouterError
from backend.core.orchestrator import execute_project


@pytest.mark.asyncio
async def test_model_router_retries_and_parses_json(monkeypatch):
    attempts = {"count": 0}

    async def fake_complete(self, **kwargs):
        attempts["count"] += 1
        if attempts["count"] < 3:
            return "not valid json"
        return '{"tasks":[{"role":"backend_engineer","description":"Build API"}]}'

    monkeypatch.setattr(LLMClient, "complete", fake_complete)

    router = ModelRouter(max_retries=3, retry_backoff_seconds=0.0)
    payload = await router.call_team_lead("Build a service", "system")

    assert attempts["count"] == 3
    assert payload["tasks"][0]["role"] == "backend_engineer"


@pytest.mark.asyncio
async def test_model_router_respects_retry_cap(monkeypatch):
    async def fake_complete(self, **kwargs):
        return "still invalid"

    monkeypatch.setattr(LLMClient, "complete", fake_complete)

    router = ModelRouter(max_retries=99, retry_backoff_seconds=0.0)

    with pytest.raises(ModelRouterError):
        await router.call_team_lead("Build a service", "system")


@pytest.mark.asyncio
async def test_execute_project_runs_role_bound_flow(monkeypatch):
    async def fake_team_lead(self, prompt, system_prompt):
        return {
            "tasks": [
                {"role": "backend_engineer", "description": "Build backend"},
                {"role": "frontend_engineer", "description": "Build frontend"},
                {"role": "database_engineer", "description": "Design schema"},
            ]
        }

    async def fake_backend(self, prompt, system_prompt):
        return {"files_created": ["backend/app.py"], "files_modified": [], "code": {"backend/app.py": "print('ok')"}}

    async def fake_frontend(self, prompt, system_prompt):
        return {"files_created": ["frontend/App.tsx"], "files_modified": [], "code": {"frontend/App.tsx": "export default function App() { return null }"}}

    async def fake_database(self, prompt, system_prompt):
        return {"files_created": ["db/schema.sql"], "files_modified": [], "schema": {"tables": ["users"]}, "migrations": []}

    async def fake_qa(self, prompt, system_prompt):
        return {"pass": True, "issues": []}

    monkeypatch.setattr(ModelRouter, "call_team_lead", fake_team_lead)
    monkeypatch.setattr(ModelRouter, "call_backend_engineer", fake_backend)
    monkeypatch.setattr(ModelRouter, "call_frontend_engineer", fake_frontend)
    monkeypatch.setattr(ModelRouter, "call_database_engineer", fake_database)
    monkeypatch.setattr(ModelRouter, "call_qa_engineer", fake_qa)

    result = await execute_project("Build a full-stack app")

    assert result["success"] is True
    assert result["validation"]["pass"] is True
    assert len(result["results"]["backend"]) == 1
    assert len(result["results"]["frontend"]) == 1
    assert len(result["results"]["database"]) == 1


@pytest.mark.asyncio
async def test_execute_project_limits_revision_loops(monkeypatch):
    qa_calls = {"count": 0}

    async def fake_team_lead(self, prompt, system_prompt):
        return {"tasks": [{"role": "backend_engineer", "description": "Build backend"}]}

    async def fake_backend(self, prompt, system_prompt):
        return {"files_created": ["backend/app.py"], "files_modified": [], "code": {"backend/app.py": "print('ok')"}}

    async def fake_qa(self, prompt, system_prompt):
        qa_calls["count"] += 1
        return {"pass": False, "issues": ["Fix issue"]}

    monkeypatch.setattr(ModelRouter, "call_team_lead", fake_team_lead)
    monkeypatch.setattr(ModelRouter, "call_backend_engineer", fake_backend)
    monkeypatch.setattr(ModelRouter, "call_frontend_engineer", fake_backend)
    monkeypatch.setattr(ModelRouter, "call_database_engineer", fake_backend)
    monkeypatch.setattr(ModelRouter, "call_qa_engineer", fake_qa)

    result = await execute_project("Build an API", max_revision_loops=2)

    assert result["success"] is False
    assert result["revisions_used"] == 2
    assert qa_calls["count"] == 3  # initial QA + 2 revision checks


@pytest.mark.asyncio
async def test_execute_project_emits_streaming_events(monkeypatch):
    events = []

    async def fake_team_lead(self, prompt, system_prompt):
        return {"tasks": [{"role": "backend_engineer", "description": "Build backend"}]}

    async def fake_backend(self, prompt, system_prompt):
        return {"files_created": ["backend/app.py"], "files_modified": [], "code": {"backend/app.py": "print('ok')"}}

    async def fake_qa(self, prompt, system_prompt):
        return {"pass": True, "issues": []}

    monkeypatch.setattr(ModelRouter, "call_team_lead", fake_team_lead)
    monkeypatch.setattr(ModelRouter, "call_backend_engineer", fake_backend)
    monkeypatch.setattr(ModelRouter, "call_frontend_engineer", fake_backend)
    monkeypatch.setattr(ModelRouter, "call_database_engineer", fake_backend)
    monkeypatch.setattr(ModelRouter, "call_qa_engineer", fake_qa)

    async def on_event(event_name, payload):
        events.append(event_name)

    result = await execute_project("Build API", on_event=on_event, project_id="proj_1")

    assert result["success"] is True
    assert "run_started" in events
    assert "agent_started" in events
    assert "run_finished" in events
