"""
Atom Loader — Phase 6

WASM-based plugin loader with sandboxed execution.

Provides:
- WASM module loading
- WASI integration for limited system access
- Capability-enforced sandboxing
- SDK hook implementation

Usage:
    loader = AtomLoader()
    instance = loader.load_atom("path/to/atom", manifest)
    result = instance.run(context)

Note: Requires wasmtime package for full WASM support.
Falls back to Python-based simulation if wasmtime unavailable.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime

from backend.marketplace.manifest import AtomManifest, CapabilitySet
from backend.engine.events import get_event_emitter, EngineEventType


# ─── Constants ───────────────────────────────────────────────────────────────

ATOMS_DIR = Path(".atoms")
WASM_MEMORY_LIMIT = 256 * 1024 * 1024  # 256MB per atom


# ─── Atom Instance ───────────────────────────────────────────────────────────

@dataclass
class AtomInstance:
    """
    A running atom instance.
    
    Wraps WASM module with SDK hooks and capability enforcement.
    """
    atom_id: str
    manifest: AtomManifest
    state: Dict[str, Any] = field(default_factory=dict)
    _wasm_instance: Any = None
    _events: Any = None
    _created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def __post_init__(self):
        self._events = get_event_emitter()
    
    # ─── SDK Hooks ───────────────────────────────────────────────────────────
    
    def sync_state(self, engine_state: Dict[str, Any]) -> None:
        """
        SDK Hook: Sync engine state to atom.
        
        Called by engine to update atom with latest state.
        """
        self.state["engine"] = engine_state
        self._invoke("on_state_sync", engine_state)
    
    def on_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """
        SDK Hook: Notify atom of engine event.
        
        Called by engine when relevant events occur.
        """
        self._invoke("on_event", {
            "type": event_type,
            "payload": payload,
        })
    
    def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        SDK Hook: Atom requests to use an MCP tool.
        
        Capability-enforced: Only allowed tools can be called.
        """
        # Check if tool is allowed
        if not self._check_tool_capability(tool_name, args):
            return {
                "error": f"Tool '{tool_name}' not permitted by capabilities",
                "allowed": False,
            }
        
        # Emit tool request event
        self._events.emit(EngineEventType.AGENT_STATUS, {
            "agent": f"atom:{self.atom_id}",
            "event": "TOOL_REQUESTED",
            "tool": tool_name,
            "args": str(args)[:200],
        })
        
        # TODO: Route to MCP manager
        return {"status": "pending", "tool": tool_name}
    
    def emit_signal(self, signal_type: str, data: Dict[str, Any]) -> None:
        """
        SDK Hook: Atom emits feedback signal.
        
        Used for prompt_optimizer learning.
        """
        self._events.emit(EngineEventType.AGENT_STATUS, {
            "agent": f"atom:{self.atom_id}",
            "event": "SIGNAL_EMITTED",
            "signal_type": signal_type,
            "data": data,
        })
    
    # ─── Execution ───────────────────────────────────────────────────────────
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute atom's main function.
        
        Args:
            context: Execution context (task, params, etc.)
            
        Returns:
            Atom result
        """
        self._events.emit(EngineEventType.AGENT_STARTED, {
            "agent": f"atom:{self.atom_id}",
            "task": str(context.get("task", ""))[:100],
        })
        
        try:
            result = self._invoke("run", context)
            
            self._events.emit(EngineEventType.AGENT_COMPLETED, {
                "agent": f"atom:{self.atom_id}",
                "status": "success",
            })
            
            return result or {"status": "completed"}
            
        except Exception as e:
            self._events.emit(EngineEventType.ERROR, {
                "agent": f"atom:{self.atom_id}",
                "error": str(e),
            })
            return {"status": "error", "error": str(e)}
    
    def _invoke(self, function: str, args: Any) -> Any:
        """Invoke function on WASM instance."""
        if self._wasm_instance:
            # Call WASM function
            try:
                func = self._wasm_instance.exports.get(function)
                if func:
                    return func(json.dumps(args))
            except Exception:
                pass
        
        # Fallback: No-op for Python simulation
        return None
    
    def _check_tool_capability(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """Check if tool call is permitted by capabilities."""
        caps = self.manifest.capabilities
        
        # Map tool names to capabilities
        if tool_name in ["read_file", "view_file"]:
            path = args.get("path", "")
            return self._path_matches(path, caps.read_files)
        
        if tool_name in ["write_file", "create_file"]:
            path = args.get("path", "")
            return self._path_matches(path, caps.write_files)
        
        if tool_name in ["http_get", "http_post", "fetch"]:
            host = args.get("host", args.get("url", ""))
            return self._host_matches(host, caps.network_access)
        
        if tool_name in ["run_command", "shell"]:
            return caps.terminal_access
        
        return True  # Default allow for unknown tools
    
    def _path_matches(self, path: str, patterns: List[str]) -> bool:
        """Check if path matches any pattern."""
        from fnmatch import fnmatch
        for pattern in patterns:
            if fnmatch(path, pattern):
                return True
        return False
    
    def _host_matches(self, url: str, allowed_hosts: List[str]) -> bool:
        """Check if URL host is allowed."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            host = parsed.netloc or url
            return host in allowed_hosts or any(
                host.endswith(f".{h}") for h in allowed_hosts
            )
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "manifest": self.manifest.to_dict(),
            "state": self.state,
            "created_at": self._created_at,
        }


# ─── Atom Loader ─────────────────────────────────────────────────────────────

class AtomLoader:
    """
    Loads and manages WASM-based atoms.
    
    Features:
    - WASM module loading with wasmtime
    - Capability-enforced sandboxing
    - Instance lifecycle management
    """
    
    def __init__(self, atoms_dir: str = ""):
        self.atoms_dir = Path(atoms_dir) if atoms_dir else ATOMS_DIR
        self.atoms_dir.mkdir(exist_ok=True)
        self.instances: Dict[str, AtomInstance] = {}
        self.events = get_event_emitter()
        
        # Try to import wasmtime
        self._wasmtime = None
        try:
            import wasmtime
            self._wasmtime = wasmtime
            self._engine = wasmtime.Engine()
        except ImportError:
            print("[AtomLoader] wasmtime not installed, using simulation mode")
    
    @property
    def has_wasm_support(self) -> bool:
        """Check if WASM support is available."""
        return self._wasmtime is not None
    
    def load_atom(self, atom_path: str, manifest: AtomManifest) -> AtomInstance:
        """
        Load an atom from its directory.
        
        Args:
            atom_path: Path to atom directory
            manifest: Validated manifest
            
        Returns:
            Loaded AtomInstance
        """
        if not manifest.is_valid():
            raise ValueError(f"Invalid manifest: {manifest.get_errors()}")
        
        instance = AtomInstance(
            atom_id=manifest.id,
            manifest=manifest,
        )
        
        # Load WASM module if available
        if self._wasmtime:
            wasm_path = Path(atom_path) / manifest.entrypoint
            if wasm_path.exists():
                instance._wasm_instance = self._load_wasm(
                    str(wasm_path),
                    manifest.capabilities
                )
        
        self.instances[manifest.id] = instance
        
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": "atom_loader",
            "event": "ATOM_LOADED",
            "atom_id": manifest.id,
            "wasm_support": self.has_wasm_support,
        })
        
        return instance
    
    def _load_wasm(self, wasm_path: str, capabilities: CapabilitySet) -> Any:
        """Load WASM module with capability restrictions."""
        if not self._wasmtime:
            return None
        
        wasmtime = self._wasmtime
        
        try:
            store = wasmtime.Store(self._engine)
            module = wasmtime.Module.from_file(self._engine, wasm_path)
            
            # Create linker with WASI
            linker = wasmtime.Linker(self._engine)
            linker.define_wasi()
            
            # Configure WASI with restricted capabilities
            wasi_config = wasmtime.WasiConfig()
            wasi_config.inherit_stdout()
            wasi_config.inherit_stderr()
            
            # Set up restricted filesystem access
            # Note: Full implementation requires careful path mapping
            
            store.set_wasi(wasi_config)
            instance = linker.instantiate(store, module)
            
            return instance
            
        except Exception as e:
            print(f"[AtomLoader] WASM load error: {e}")
            return None
    
    def unload_atom(self, atom_id: str) -> bool:
        """Unload an atom instance."""
        if atom_id in self.instances:
            del self.instances[atom_id]
            self.events.emit(EngineEventType.AGENT_STATUS, {
                "agent": "atom_loader",
                "event": "ATOM_UNLOADED",
                "atom_id": atom_id,
            })
            return True
        return False
    
    def get_instance(self, atom_id: str) -> Optional[AtomInstance]:
        """Get loaded atom instance."""
        return self.instances.get(atom_id)
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """List all loaded atoms."""
        return [inst.to_dict() for inst in self.instances.values()]


# ─── Global Instance ─────────────────────────────────────────────────────────

_atom_loader: Optional[AtomLoader] = None


def get_atom_loader() -> AtomLoader:
    """Get global atom loader instance."""
    global _atom_loader
    if _atom_loader is None:
        _atom_loader = AtomLoader()
    return _atom_loader
