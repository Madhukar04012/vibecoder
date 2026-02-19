"""Tests for Sandbox Manager."""

import os
import pytest
from backend.engine.sandbox import SandboxManager, Sandbox


class TestSandbox:
    """Tests for individual sandbox instances."""
    
    def setup_method(self):
        self.mgr = SandboxManager()
    
    def test_create_sandbox(self):
        sandbox = self.mgr.create_sandbox("test")
        assert sandbox.id.startswith("test_")
        assert os.path.isdir(sandbox.path)
        self.mgr.destroy_sandbox(sandbox.id)
    
    def test_write_and_read_file(self):
        sandbox = self.mgr.create_sandbox("rw")
        sandbox.write_file("hello.py", "print('hello')")
        
        content = sandbox.read_file("hello.py")
        assert content == "print('hello')"
        
        self.mgr.destroy_sandbox(sandbox.id)
    
    def test_list_files(self):
        sandbox = self.mgr.create_sandbox("ls")
        sandbox.write_file("a.py", "a")
        sandbox.write_file("dir/b.py", "b")
        
        files = sandbox.list_files()
        assert "a.py" in files
        assert "dir/b.py" in files
        
        self.mgr.destroy_sandbox(sandbox.id)
    
    def test_execute_command(self):
        sandbox = self.mgr.create_sandbox("exec")
        sandbox.write_file("test.py", "print('works')")
        
        result = sandbox.execute("python test.py", timeout=10)
        assert result.success
        assert "works" in result.stdout
        
        self.mgr.destroy_sandbox(sandbox.id)
    
    def test_execute_timeout(self):
        sandbox = self.mgr.create_sandbox("timeout")
        sandbox.write_file("slow.py", "import time; time.sleep(30)")
        
        result = sandbox.execute("python slow.py", timeout=2)
        assert not result.success
        assert "timed out" in result.stderr.lower()
        
        self.mgr.destroy_sandbox(sandbox.id)
    
    def test_context_manager(self):
        path = None
        with self.mgr.create("ctx") as sandbox:
            path = sandbox.path
            assert os.path.isdir(path)
        
        # Should be cleaned up
        assert not os.path.isdir(path)
    
    def test_cleanup_removes_directory(self):
        sandbox = self.mgr.create_sandbox("cleanup")
        path = sandbox.path
        self.mgr.destroy_sandbox(sandbox.id)
        assert not os.path.isdir(path)
    
    def test_collect_results(self):
        sandbox = self.mgr.create_sandbox("collect")
        sandbox.write_file("out.txt", "result data")
        
        results = sandbox.collect_results()
        assert "out.txt" in results
        assert results["out.txt"] == "result data"
        
        self.mgr.destroy_sandbox(sandbox.id)


class TestSandboxManager:
    """Tests for sandbox manager."""
    
    def setup_method(self):
        self.mgr = SandboxManager()
    
    def test_list_active(self):
        s1 = self.mgr.create_sandbox("a")
        s2 = self.mgr.create_sandbox("b")
        
        active = self.mgr.list_active()
        assert len(active) >= 2
        
        self.mgr.cleanup_all()
    
    def test_cleanup_all(self):
        self.mgr.create_sandbox("c1")
        self.mgr.create_sandbox("c2")
        
        count = self.mgr.cleanup_all()
        assert count >= 2
        assert len(self.mgr.list_active()) == 0
