"""End-to-end smoke tests for unified pipeline guarantees."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app


def test_cli_smoke_generate_builds_files(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    output_dir = tmp_path / "cli-smoke"

    cmd = [
        sys.executable,
        "cli.py",
        "generate",
        "simple todo app",
        "--simple",
        "--build",
        "--output",
        str(output_dir),
        "--tier",
        "enterprise",
        "--project-id",
        "smoke-cli",
        "--memory-scope",
        "project",
    ]

    env = os.environ.copy()
    env["NIM_API_KEY"] = ""
    env["OPENROUTER_API_KEY"] = ""
    env["TEAM_LEAD_LLM_ROUTING"] = "false"

    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )

    assert proc.returncode == 0, f"CLI failed\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    files = [path for path in output_dir.rglob("*") if path.is_file()]
    assert len(files) > 5, f"Expected >5 files, found {len(files)}"


def test_api_smoke_generate_completes(monkeypatch):
    monkeypatch.setenv("NIM_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("TEAM_LEAD_LLM_ROUTING", "false")

    client = TestClient(app)

    response = client.post(
        "/generate/project",
        json={
            "idea": "simple todo app",
            "mode": "simple",
            "token_tier": "enterprise",
            "project_id": "smoke-api",
            "memory_scope": "project",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    data = payload["data"]

    assert data["state"] in {"completed", "partial_success"}
    assert data["success"] is True

    manifest = data.get("artifact_manifest") or {}
    assert int(manifest.get("file_count", 0)) > 5
