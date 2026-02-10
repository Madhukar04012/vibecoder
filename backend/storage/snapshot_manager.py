"""
Snapshot Manager — Phase 5

Time Travel Foundation: Global undo for entire system state.

Captures:
- VFS (files)
- Agent memory
- Engine state
- Terminal state

Usage:
    snapshots = SnapshotManager()
    snap_id = snapshots.create_snapshot("pre_execution", engine.export_state())
    snapshots.restore_snapshot(snap_id, target_path)

Enforced:
- ❌ No collaboration without snapshots
- ❌ No destructive action without snapshot
"""

import uuid
import json
import shutil
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


# ─── Constants ───────────────────────────────────────────────────────────────

SNAPSHOT_ROOT = Path(".snapshots")
MAX_SNAPSHOTS = 50  # Keep last 50 snapshots


# ─── Snapshot Metadata ───────────────────────────────────────────────────────

@dataclass
class SnapshotMeta:
    """Metadata for a snapshot."""
    id: str
    label: str
    timestamp: str
    engine_state: str  # JSON string of engine state key
    size_bytes: int = 0
    file_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "timestamp": self.timestamp,
            "engine_state": self.engine_state,
            "size_bytes": self.size_bytes,
            "file_count": self.file_count,
        }


# ─── Snapshot Manager ────────────────────────────────────────────────────────

class SnapshotManager:
    """
    Global undo system for VibeCoder.
    
    Provides full-system rollback capabilities:
    - Filesystem snapshots
    - Engine state preservation
    - Agent memory backup
    """
    
    def __init__(self, root: str = ""):
        self.root = Path(root) if root else SNAPSHOT_ROOT
        self.root.mkdir(exist_ok=True)
        self._snapshots: Dict[str, SnapshotMeta] = {}
        self._load_existing()
    
    def _load_existing(self) -> None:
        """Load metadata for existing snapshots."""
        for snap_dir in self.root.iterdir():
            if snap_dir.is_dir():
                meta_file = snap_dir / "meta.json"
                if meta_file.exists():
                    try:
                        data = json.loads(meta_file.read_text())
                        self._snapshots[data["id"]] = SnapshotMeta(**data)
                    except Exception:
                        pass
    
    def create_snapshot(
        self,
        label: str,
        state: Dict[str, Any],
        vfs_path: str = "",
    ) -> str:
        """
        Create a full system snapshot.
        
        Args:
            label: Human-readable label (e.g., "pre_execution")
            state: Engine/agent state dict
            vfs_path: Path to virtual filesystem to backup
            
        Returns:
            Snapshot ID
        """
        # Generate unique ID
        timestamp = datetime.utcnow().isoformat()
        snap_id = f"{timestamp.replace(':', '-')}_{label}_{uuid.uuid4().hex[:6]}"
        snap_dir = self.root / snap_id
        snap_dir.mkdir(parents=True, exist_ok=True)
        
        file_count = 0
        size_bytes = 0
        
        # 1. Save metadata
        meta = SnapshotMeta(
            id=snap_id,
            label=label,
            timestamp=timestamp,
            engine_state=state.get("engine_state", "unknown"),
        )
        
        # 2. Save engine + agent memory state
        state_file = snap_dir / "state.json"
        state_json = json.dumps(state, indent=2, default=str)
        state_file.write_text(state_json)
        size_bytes += len(state_json)
        
        # 3. Save filesystem (if provided)
        if vfs_path and os.path.exists(vfs_path):
            vfs_snap = snap_dir / "vfs"
            try:
                shutil.copytree(
                    vfs_path,
                    vfs_snap,
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(
                        '.git', '__pycache__', 'node_modules', '.snapshots'
                    )
                )
                # Count files and size
                for root, dirs, files in os.walk(vfs_snap):
                    for f in files:
                        file_path = os.path.join(root, f)
                        size_bytes += os.path.getsize(file_path)
                        file_count += 1
            except Exception as e:
                # Log but don't fail
                print(f"[Snapshot] VFS backup warning: {e}")
        
        # Update meta with stats
        meta.size_bytes = size_bytes
        meta.file_count = file_count
        
        # Save metadata
        (snap_dir / "meta.json").write_text(json.dumps(meta.to_dict(), indent=2))
        self._snapshots[snap_id] = meta
        
        # Cleanup old snapshots
        self._cleanup_old()
        
        return snap_id
    
    def restore_snapshot(
        self,
        snap_id: str,
        target_path: str = "",
    ) -> Dict[str, Any]:
        """
        Restore system from snapshot.
        
        Args:
            snap_id: Snapshot ID to restore
            target_path: Where to restore VFS (optional)
            
        Returns:
            Restored state dict
        """
        snap_dir = self.root / snap_id
        if not snap_dir.exists():
            raise ValueError(f"Snapshot not found: {snap_id}")
        
        # 1. Load state
        state_file = snap_dir / "state.json"
        state = json.loads(state_file.read_text())
        
        # 2. Restore VFS if target provided
        vfs_snap = snap_dir / "vfs"
        if target_path and vfs_snap.exists():
            if os.path.exists(target_path):
                shutil.rmtree(target_path, ignore_errors=True)
            shutil.copytree(vfs_snap, target_path)
        
        return state
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all available snapshots."""
        snapshots = []
        for snap_id, meta in sorted(
            self._snapshots.items(),
            key=lambda x: x[1].timestamp,
            reverse=True
        ):
            snapshots.append(meta.to_dict())
        return snapshots
    
    def get_snapshot(self, snap_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific snapshot."""
        if snap_id in self._snapshots:
            return self._snapshots[snap_id].to_dict()
        return None
    
    def delete_snapshot(self, snap_id: str) -> bool:
        """Delete a snapshot."""
        snap_dir = self.root / snap_id
        if snap_dir.exists():
            shutil.rmtree(snap_dir)
            if snap_id in self._snapshots:
                del self._snapshots[snap_id]
            return True
        return False
    
    def _cleanup_old(self) -> None:
        """Remove oldest snapshots if over limit."""
        if len(self._snapshots) > MAX_SNAPSHOTS:
            sorted_snaps = sorted(
                self._snapshots.items(),
                key=lambda x: x[1].timestamp
            )
            to_remove = len(sorted_snaps) - MAX_SNAPSHOTS
            for snap_id, _ in sorted_snaps[:to_remove]:
                self.delete_snapshot(snap_id)
    
    def export_state_for_snapshot(
        self,
        engine_state: str,
        prd: Optional[Dict] = None,
        roadmap: Optional[Dict] = None,
        files: Optional[Dict] = None,
        agent_memory: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Helper to build state dict for snapshot."""
        return {
            "engine_state": engine_state,
            "prd": prd or {},
            "roadmap": roadmap or {},
            "files": files or {},
            "agent_memory": agent_memory or {},
            "snapshot_version": "1.0",
        }


# ─── Global Instance ─────────────────────────────────────────────────────────

_snapshot_manager: Optional[SnapshotManager] = None


def get_snapshot_manager() -> SnapshotManager:
    """Get global snapshot manager instance."""
    global _snapshot_manager
    if _snapshot_manager is None:
        _snapshot_manager = SnapshotManager()
    return _snapshot_manager


# ─── Convenience Functions ───────────────────────────────────────────────────

def create_snapshot(label: str, state: Dict[str, Any], vfs_path: str = "") -> str:
    """Create a snapshot."""
    return get_snapshot_manager().create_snapshot(label, state, vfs_path)


def restore_snapshot(snap_id: str, target_path: str = "") -> Dict[str, Any]:
    """Restore from a snapshot."""
    return get_snapshot_manager().restore_snapshot(snap_id, target_path)


def list_snapshots() -> List[Dict[str, Any]]:
    """List all snapshots."""
    return get_snapshot_manager().list_snapshots()
