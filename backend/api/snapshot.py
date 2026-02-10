"""
Snapshot API — Phase 5

REST API for time-travel snapshots.

Endpoints:
- POST /api/snapshots — Create snapshot
- GET  /api/snapshots — List snapshots
- POST /api/snapshots/{id}/restore — Restore snapshot
- GET  /api/snapshots/{id} — Get snapshot details
- DELETE /api/snapshots/{id} — Delete snapshot
- GET  /api/snapshots/diff/{a}/{b} — Compare snapshots
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.engine.snapshot_manager import get_snapshot_manager
from backend.engine.atoms_engine import get_current_cost


router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])


class CreateSnapshotRequest(BaseModel):
    project_path: str
    label: str = ""


class RestoreSnapshotRequest(BaseModel):
    target_path: str


@router.post("")
def create_snapshot(req: CreateSnapshotRequest):
    """Create a system snapshot."""
    mgr = get_snapshot_manager()
    
    try:
        cost_summary = get_current_cost()
        snapshot_id = mgr.create_snapshot(
            project_path=req.project_path,
            engine_state="idle",
            token_summary=cost_summary,
            label=req.label,
        )
        return {
            "snapshot_id": snapshot_id,
            "message": "Snapshot created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
def list_snapshots():
    """List all snapshots."""
    mgr = get_snapshot_manager()
    return {"snapshots": mgr.list_snapshots()}


@router.get("/{snapshot_id}")
def get_snapshot(snapshot_id: str):
    """Get snapshot details."""
    mgr = get_snapshot_manager()
    meta = mgr.get_snapshot(snapshot_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Snapshot '{snapshot_id}' not found")
    return meta


@router.post("/{snapshot_id}/restore")
def restore_snapshot(snapshot_id: str, req: RestoreSnapshotRequest):
    """Restore a snapshot."""
    mgr = get_snapshot_manager()
    
    try:
        result = mgr.restore_snapshot(snapshot_id, req.target_path)
        return {
            "message": "Snapshot restored successfully",
            **result,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{snapshot_id}")
def delete_snapshot(snapshot_id: str):
    """Delete a snapshot."""
    mgr = get_snapshot_manager()
    if mgr.delete_snapshot(snapshot_id):
        return {"message": f"Snapshot '{snapshot_id}' deleted"}
    raise HTTPException(status_code=404, detail=f"Snapshot '{snapshot_id}' not found")


@router.get("/diff/{snap_a}/{snap_b}")
def diff_snapshots(snap_a: str, snap_b: str):
    """Compare two snapshots."""
    mgr = get_snapshot_manager()
    
    try:
        diff = mgr.diff_snapshots(snap_a, snap_b)
        return diff
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
