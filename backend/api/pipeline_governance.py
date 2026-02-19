"""
Pipeline governance API.

Operational controls for observability, memory governance, and artifact lifecycle.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.engine.observability import get_agent_stats
from backend.engine.token_governance import get_token_governance
from backend.memory.indexer import clear_index, get_index_stats, list_scopes
from backend.storage.artifact_store import get_artifact_store


router = APIRouter(prefix="/api/pipeline", tags=["pipeline-governance"])


@router.get("/agent-stats")
def agent_stats():
    return get_agent_stats()


@router.get("/memory/scopes")
def memory_scopes():
    scopes = list_scopes()
    return {
        "scopes": scopes,
        "stats": {scope: get_index_stats(scope_key=scope) for scope in scopes},
    }


@router.delete("/memory/scopes/{scope_key}")
def clear_memory_scope(scope_key: str):
    clear_index(scope_key=scope_key)
    return {"cleared": scope_key}


@router.get("/artifacts/{project_key}/versions")
def list_artifact_versions(project_key: str):
    versions = get_artifact_store().list_versions(project_key)
    return {"project_key": project_key, "versions": versions}


@router.get("/artifacts/{project_key}/bundle/{version}")
def download_artifact_bundle(project_key: str, version: int):
    try:
        bundle_path = get_artifact_store().get_bundle_path(project_key, version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    filename = f"{project_key}-v{version}.zip"
    return FileResponse(path=str(bundle_path), filename=filename, media_type="application/zip")


@router.post("/artifacts/{project_key}/regenerate/{version}")
def regenerate_from_artifact(project_key: str, version: int):
    store = get_artifact_store()
    try:
        files = store.load_version(project_key, version)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    manifest = store.persist(
        project_key=project_key,
        run_id=f"regenerate_v{version}",
        files=files,
        metadata={"source_version": version, "regenerated": True},
    )
    return {
        "project_key": project_key,
        "source_version": version,
        "new_version": manifest.version,
        "file_count": manifest.file_count,
        "bundle_path": manifest.bundle_path,
    }


@router.get("/budget/{user_id}")
def budget_summary(user_id: str, tier: str = Query("free", max_length=16)):
    return get_token_governance().get_summary(user_id=user_id, tier=tier)
