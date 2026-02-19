"""
Snapshot Manager — Phase 5

Full system snapshots for time-travel debugging.
Captures everything: files, engine state, agent memory, token ledger.

One-click restore to any previous point in time.

Usage:
    from engine.snapshot_manager import get_snapshot_manager

    mgr = get_snapshot_manager()
    
    # Take snapshot
    snapshot_id = mgr.create_snapshot(label="before_refactor")
    
    # ... make changes ...
    
    # Restore
    mgr.restore_snapshot(snapshot_id)
"""

import json
import os
import shutil
import uuid
import zipfile
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from backend.engine.events import get_event_emitter, EngineEventType


# ─── Constants ──────────────────────────────────────────────────────────────

MAX_SNAPSHOTS = 50  # Maximum snapshots to keep
SNAPSHOT_DIR = "snapshots"


# ─── Snapshot Metadata ──────────────────────────────────────────────────────

@dataclass
class SnapshotMeta:
    """Metadata for a system snapshot."""
    id: str
    label: str
    created_at: str
    file_count: int
    total_size_bytes: int
    engine_state: str
    token_cost: float
    archive_path: str
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "created_at": self.created_at,
            "file_count": self.file_count,
            "total_size_bytes": self.total_size_bytes,
            "engine_state": self.engine_state,
            "token_cost": round(self.token_cost, 6),
        }


# ─── Snapshot Manager ───────────────────────────────────────────────────────

class SnapshotManager:
    """
    Full system snapshot and restore.
    
    Captures:
    - All project files
    - Engine state machine state
    - Token ledger data
    - Semantic index stats
    - Agent configuration
    
    Storage: ZIP archive + JSON metadata
    """
    
    def __init__(self, storage_path: str = SNAPSHOT_DIR):
        self.storage_path = storage_path
        self._snapshots: Dict[str, SnapshotMeta] = {}
        self.events = get_event_emitter()
        
        os.makedirs(storage_path, exist_ok=True)
        self._load_index()
    
    def create_snapshot(
        self,
        project_path: str,
        engine_state: str = "idle",
        token_summary: Optional[Dict[str, Any]] = None,
        label: str = "",
    ) -> str:
        """
        Create a full system snapshot.
        
        Args:
            project_path: Path to project directory
            engine_state: Current engine state
            token_summary: Token ledger summary dict
            label: Human-readable label
            
        Returns:
            Snapshot ID
        """
        snapshot_id = f"snap_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        archive_path = os.path.join(self.storage_path, f"{snapshot_id}.zip")
        meta_path = os.path.join(self.storage_path, f"{snapshot_id}.json")
        
        file_count = 0
        total_size = 0
        
        # Create ZIP archive of project files
        exclude_dirs = {"__pycache__", "node_modules", ".git", ".venv", ".env", "snapshots"}
        exclude_exts = {".pyc", ".db", ".sqlite", ".sqlite3"}
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if os.path.isdir(project_path):
                for root, dirs, files in os.walk(project_path):
                    # Skip excluded directories
                    dirs[:] = [d for d in dirs if d not in exclude_dirs]
                    
                    for filename in files:
                        if any(filename.endswith(ext) for ext in exclude_exts):
                            continue
                        
                        filepath = os.path.join(root, filename)
                        rel_path = os.path.relpath(filepath, project_path)
                        
                        try:
                            file_size = os.path.getsize(filepath)
                            if file_size > 5_000_000:  # Skip files > 5MB
                                continue
                            
                            zf.write(filepath, f"files/{rel_path}")
                            file_count += 1
                            total_size += file_size
                        except (PermissionError, OSError):
                            pass
            
            # Store engine state as JSON inside the ZIP
            state_data = {
                "engine_state": engine_state,
                "token_summary": token_summary or {},
                "snapshot_time": datetime.utcnow().isoformat(),
            }
            zf.writestr("state.json", json.dumps(state_data, indent=2))
        
        # Create metadata
        meta = SnapshotMeta(
            id=snapshot_id,
            label=label or f"Snapshot {len(self._snapshots) + 1}",
            created_at=datetime.utcnow().isoformat(),
            file_count=file_count,
            total_size_bytes=total_size,
            engine_state=engine_state,
            token_cost=token_summary.get("total_cost_usd", 0) if token_summary else 0,
            archive_path=archive_path,
        )
        
        # Save metadata
        with open(meta_path, 'w') as f:
            json.dump(meta.to_dict(), f, indent=2)
        
        self._snapshots[snapshot_id] = meta
        
        # Enforce limit
        self._prune_old_snapshots()
        
        self._emit_event("SNAPSHOT_CREATED", {
            "snapshot_id": snapshot_id,
            "label": meta.label,
            "file_count": file_count,
        })
        
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str, target_path: str) -> Dict[str, Any]:
        """
        Restore a snapshot to the target path.
        
        Args:
            snapshot_id: ID of snapshot to restore
            target_path: Where to restore files
            
        Returns:
            Dict with restore details
        """
        meta = self._snapshots.get(snapshot_id)
        if not meta:
            raise ValueError(f"Snapshot '{snapshot_id}' not found")
        
        if not os.path.exists(meta.archive_path):
            raise FileNotFoundError(f"Snapshot archive not found: {meta.archive_path}")
        
        restored_count = 0
        state_data = {}
        
        with zipfile.ZipFile(meta.archive_path, 'r') as zf:
            for info in zf.infolist():
                if info.filename.startswith("files/"):
                    rel_path = info.filename[6:]  # Remove "files/" prefix
                    if not rel_path:
                        continue
                    
                    target = os.path.join(target_path, rel_path)
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    
                    with zf.open(info) as src, open(target, 'wb') as dst:
                        dst.write(src.read())
                    restored_count += 1
                
                elif info.filename == "state.json":
                    state_data = json.loads(zf.read(info))
        
        self._emit_event("SNAPSHOT_RESTORED", {
            "snapshot_id": snapshot_id,
            "files_restored": restored_count,
        })
        
        return {
            "snapshot_id": snapshot_id,
            "files_restored": restored_count,
            "engine_state": state_data.get("engine_state", "idle"),
            "token_summary": state_data.get("token_summary", {}),
        }
    
    def list_snapshots(self) -> List[dict]:
        """List all available snapshots (newest first)."""
        return sorted(
            [m.to_dict() for m in self._snapshots.values()],
            key=lambda x: x["created_at"],
            reverse=True,
        )
    
    def get_snapshot(self, snapshot_id: str) -> Optional[dict]:
        """Get metadata for a specific snapshot."""
        meta = self._snapshots.get(snapshot_id)
        return meta.to_dict() if meta else None
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot."""
        meta = self._snapshots.get(snapshot_id)
        if not meta:
            return False
        
        # Remove files
        try:
            if os.path.exists(meta.archive_path):
                os.remove(meta.archive_path)
            meta_path = meta.archive_path.replace('.zip', '.json')
            if os.path.exists(meta_path):
                os.remove(meta_path)
        except OSError:
            pass
        
        del self._snapshots[snapshot_id]
        return True
    
    def diff_snapshots(self, snap_a: str, snap_b: str) -> Dict[str, Any]:
        """
        Compare two snapshots.
        
        Returns:
            Dict with added, removed, and modified files
        """
        files_a = self._list_archive_files(snap_a)
        files_b = self._list_archive_files(snap_b)
        
        set_a = set(files_a.keys())
        set_b = set(files_b.keys())
        
        added = list(set_b - set_a)
        removed = list(set_a - set_b)
        
        modified = []
        for f in set_a & set_b:
            if files_a[f] != files_b[f]:
                modified.append(f)
        
        return {
            "snapshot_a": snap_a,
            "snapshot_b": snap_b,
            "added": sorted(added),
            "removed": sorted(removed),
            "modified": sorted(modified),
            "unchanged": len(set_a & set_b) - len(modified),
        }
    
    def _list_archive_files(self, snapshot_id: str) -> Dict[str, int]:
        """List files in a snapshot archive with sizes."""
        meta = self._snapshots.get(snapshot_id)
        if not meta or not os.path.exists(meta.archive_path):
            return {}
        
        files = {}
        with zipfile.ZipFile(meta.archive_path, 'r') as zf:
            for info in zf.infolist():
                if info.filename.startswith("files/"):
                    rel = info.filename[6:]
                    if rel:
                        files[rel] = info.file_size
        return files
    
    def _prune_old_snapshots(self) -> None:
        """Remove oldest snapshots if exceeding limit."""
        if len(self._snapshots) <= MAX_SNAPSHOTS:
            return
        
        # Sort by creation time, remove oldest
        sorted_snaps = sorted(
            self._snapshots.items(),
            key=lambda x: x[1].created_at,
        )
        
        while len(self._snapshots) > MAX_SNAPSHOTS:
            snap_id, _ = sorted_snaps.pop(0)
            self.delete_snapshot(snap_id)
    
    def _load_index(self) -> None:
        """Load snapshot index from disk."""
        if not os.path.isdir(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                filepath = os.path.join(self.storage_path, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    snap_id = data.get("id", filename.replace('.json', ''))
                    archive_path = os.path.join(self.storage_path, f"{snap_id}.zip")
                    
                    if os.path.exists(archive_path):
                        self._snapshots[snap_id] = SnapshotMeta(
                            id=snap_id,
                            label=data.get("label", ""),
                            created_at=data.get("created_at", ""),
                            file_count=data.get("file_count", 0),
                            total_size_bytes=data.get("total_size_bytes", 0),
                            engine_state=data.get("engine_state", "idle"),
                            token_cost=data.get("token_cost", 0),
                            archive_path=archive_path,
                        )
                except Exception:
                    pass
    
    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Emit snapshot event."""
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": "snapshot_manager",
            "event": event_type,
            **payload,
        })


# ─── Global Instance ────────────────────────────────────────────────────────

_snapshot_manager: Optional[SnapshotManager] = None


def get_snapshot_manager(storage_path: str = SNAPSHOT_DIR) -> SnapshotManager:
    """Get global snapshot manager instance."""
    global _snapshot_manager
    if _snapshot_manager is None:
        _snapshot_manager = SnapshotManager(storage_path=storage_path)
    return _snapshot_manager
