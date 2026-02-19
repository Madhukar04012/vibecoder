"""Tests for Snapshot Manager."""

import os
import shutil
import tempfile
import pytest
from backend.engine.snapshot_manager import SnapshotManager


class TestSnapshotManager:
    """Tests for snapshot create/restore/list/diff."""
    
    def setup_method(self):
        self.snap_dir = tempfile.mkdtemp(prefix="snap_test_")
        self.project_dir = tempfile.mkdtemp(prefix="proj_test_")
        self.restore_dir = tempfile.mkdtemp(prefix="restore_test_")
        self.mgr = SnapshotManager(storage_path=self.snap_dir)
        
        # Create test project files
        os.makedirs(os.path.join(self.project_dir, "src"), exist_ok=True)
        with open(os.path.join(self.project_dir, "main.py"), "w") as f:
            f.write("print('hello')")
        with open(os.path.join(self.project_dir, "src", "app.py"), "w") as f:
            f.write("class App: pass")
    
    def teardown_method(self):
        shutil.rmtree(self.snap_dir, ignore_errors=True)
        shutil.rmtree(self.project_dir, ignore_errors=True)
        shutil.rmtree(self.restore_dir, ignore_errors=True)
    
    def test_create_snapshot(self):
        snap_id = self.mgr.create_snapshot(
            project_path=self.project_dir,
            label="test_snap",
        )
        assert snap_id.startswith("snap_")
        assert os.path.exists(os.path.join(self.snap_dir, f"{snap_id}.zip"))
    
    def test_list_snapshots(self):
        self.mgr.create_snapshot(self.project_dir, label="snap1")
        self.mgr.create_snapshot(self.project_dir, label="snap2")
        
        snaps = self.mgr.list_snapshots()
        assert len(snaps) == 2
        assert snaps[0]["label"] == "snap2"  # Newest first
    
    def test_restore_snapshot(self):
        snap_id = self.mgr.create_snapshot(self.project_dir, label="restore_test")
        
        result = self.mgr.restore_snapshot(snap_id, self.restore_dir)
        
        assert result["files_restored"] == 2
        assert os.path.exists(os.path.join(self.restore_dir, "main.py"))
        assert os.path.exists(os.path.join(self.restore_dir, "src", "app.py"))
        
        # Verify content
        with open(os.path.join(self.restore_dir, "main.py")) as f:
            assert f.read() == "print('hello')"
    
    def test_delete_snapshot(self):
        snap_id = self.mgr.create_snapshot(self.project_dir, label="delete_test")
        
        assert self.mgr.delete_snapshot(snap_id)
        assert self.mgr.get_snapshot(snap_id) is None
    
    def test_diff_snapshots(self):
        # Create first snapshot
        snap_a = self.mgr.create_snapshot(self.project_dir, label="before")
        
        # Modify project
        with open(os.path.join(self.project_dir, "main.py"), "w") as f:
            f.write("print('modified')")
        with open(os.path.join(self.project_dir, "new_file.py"), "w") as f:
            f.write("# new")
        
        # Create second snapshot
        snap_b = self.mgr.create_snapshot(self.project_dir, label="after")
        
        diff = self.mgr.diff_snapshots(snap_a, snap_b)
        
        assert "new_file.py" in diff["added"]
        assert "main.py" in diff["modified"]
    
    def test_snapshot_with_token_summary(self):
        token_summary = {
            "total_cost_usd": 0.05,
            "total_tokens": 1000,
        }
        snap_id = self.mgr.create_snapshot(
            self.project_dir,
            token_summary=token_summary,
            label="with_cost",
        )
        
        meta = self.mgr.get_snapshot(snap_id)
        assert meta["token_cost"] == 0.05
    
    def test_restore_nonexistent_raises(self):
        with pytest.raises(ValueError):
            self.mgr.restore_snapshot("nonexistent", self.restore_dir)
