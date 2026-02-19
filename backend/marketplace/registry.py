"""
Atom Registry — Phase 6

Tracks installed atoms and manages versions.

Provides:
- Atom installation/uninstallation
- Version tracking
- Capability approval storage
- Marketplace integration

Usage:
    registry = get_atom_registry()
    registry.install("path/to/atom")
    atoms = registry.list_installed()
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from backend.marketplace.manifest import (
    AtomManifest,
    CapabilityApproval,
    RiskLevel,
    parse_manifest,
)
from backend.engine.events import get_event_emitter, EngineEventType


# ─── Constants ───────────────────────────────────────────────────────────────

ATOMS_DIR = Path(".atoms")
REGISTRY_FILE = ATOMS_DIR / "registry.json"


# ─── Installed Atom ──────────────────────────────────────────────────────────

@dataclass
class InstalledAtom:
    """Record of an installed atom."""
    atom_id: str
    version: str
    manifest: AtomManifest
    install_path: str
    installed_at: str
    enabled: bool = True
    approval: Optional[CapabilityApproval] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "version": self.version,
            "manifest": self.manifest.to_dict(),
            "install_path": self.install_path,
            "installed_at": self.installed_at,
            "enabled": self.enabled,
            "approval": self.approval.to_dict() if self.approval else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstalledAtom":
        manifest = AtomManifest.from_dict(data["manifest"])
        approval = None
        if data.get("approval"):
            approval = CapabilityApproval(**data["approval"])
        
        return cls(
            atom_id=data["atom_id"],
            version=data["version"],
            manifest=manifest,
            install_path=data["install_path"],
            installed_at=data["installed_at"],
            enabled=data.get("enabled", True),
            approval=approval,
        )


# ─── Atom Registry ───────────────────────────────────────────────────────────

class AtomRegistry:
    """
    Manages installed atoms and their capabilities.
    
    Features:
    - Install/uninstall atoms
    - Version management
    - Capability approval tracking
    - Persistence to registry.json
    """
    
    def __init__(self, atoms_dir: str = ""):
        self.atoms_dir = Path(atoms_dir) if atoms_dir else ATOMS_DIR
        self.atoms_dir.mkdir(exist_ok=True)
        self.registry_file = self.atoms_dir / "registry.json"
        self.atoms: Dict[str, InstalledAtom] = {}
        self.events = get_event_emitter()
        
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load registry from disk."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r") as f:
                    data = json.load(f)
                    for atom_data in data.get("atoms", []):
                        atom = InstalledAtom.from_dict(atom_data)
                        self.atoms[atom.atom_id] = atom
            except Exception as e:
                print(f"[Registry] Load error: {e}")
    
    def _save_registry(self) -> None:
        """Save registry to disk."""
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.utcnow().isoformat(),
                "atoms": [atom.to_dict() for atom in self.atoms.values()],
            }
            with open(self.registry_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Registry] Save error: {e}")
    
    def install(
        self,
        source_path: str,
        approved_by: str = "system",
    ) -> InstalledAtom:
        """
        Install an atom from source directory.
        
        Args:
            source_path: Path to atom source (containing atom.yaml)
            approved_by: Who approved the installation
            
        Returns:
            InstalledAtom record
        """
        source = Path(source_path)
        manifest_path = source / "atom.yaml"
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"No atom.yaml found in {source_path}")
        
        # Parse and validate manifest
        manifest = parse_manifest(str(manifest_path))
        if not manifest.is_valid():
            raise ValueError(f"Invalid manifest: {manifest.get_errors()}")
        
        # Check if already installed
        if manifest.id in self.atoms:
            existing = self.atoms[manifest.id]
            if existing.version == manifest.version:
                raise ValueError(f"Atom {manifest.id} v{manifest.version} already installed")
        
        # Create install directory
        install_path = self.atoms_dir / manifest.id
        if install_path.exists():
            shutil.rmtree(install_path)
        shutil.copytree(source, install_path)
        
        # Create approval record
        approval = CapabilityApproval(
            atom_id=manifest.id,
            capabilities=manifest.capabilities,
            risk_level=manifest.get_risk_level(),
            approved=True,
            approved_by=approved_by,
            approved_at=datetime.utcnow().isoformat(),
        )
        
        # Create installed record
        installed = InstalledAtom(
            atom_id=manifest.id,
            version=manifest.version,
            manifest=manifest,
            install_path=str(install_path),
            installed_at=datetime.utcnow().isoformat(),
            enabled=True,
            approval=approval,
        )
        
        self.atoms[manifest.id] = installed
        self._save_registry()
        
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": "atom_registry",
            "event": "ATOM_INSTALLED",
            "atom_id": manifest.id,
            "version": manifest.version,
            "risk_level": manifest.get_risk_level().value,
        })
        
        return installed
    
    def uninstall(self, atom_id: str) -> bool:
        """Uninstall an atom."""
        if atom_id not in self.atoms:
            return False
        
        atom = self.atoms[atom_id]
        
        # Remove files
        install_path = Path(atom.install_path)
        if install_path.exists():
            shutil.rmtree(install_path)
        
        # Remove from registry
        del self.atoms[atom_id]
        self._save_registry()
        
        self.events.emit(EngineEventType.AGENT_STATUS, {
            "agent": "atom_registry",
            "event": "ATOM_UNINSTALLED",
            "atom_id": atom_id,
        })
        
        return True
    
    def enable(self, atom_id: str) -> bool:
        """Enable an installed atom."""
        if atom_id in self.atoms:
            self.atoms[atom_id].enabled = True
            self._save_registry()
            return True
        return False
    
    def disable(self, atom_id: str) -> bool:
        """Disable an installed atom."""
        if atom_id in self.atoms:
            self.atoms[atom_id].enabled = False
            self._save_registry()
            return True
        return False
    
    def get(self, atom_id: str) -> Optional[InstalledAtom]:
        """Get installed atom by ID."""
        return self.atoms.get(atom_id)
    
    def list_installed(self) -> List[Dict[str, Any]]:
        """List all installed atoms."""
        return [atom.to_dict() for atom in self.atoms.values()]
    
    def list_enabled(self) -> List[InstalledAtom]:
        """List enabled atoms."""
        return [atom for atom in self.atoms.values() if atom.enabled]
    
    def get_by_risk(self, risk_level: RiskLevel) -> List[InstalledAtom]:
        """Get atoms by risk level."""
        return [
            atom for atom in self.atoms.values()
            if atom.manifest.get_risk_level() == risk_level
        ]


# ─── Global Instance ─────────────────────────────────────────────────────────

_atom_registry: Optional[AtomRegistry] = None


def get_atom_registry() -> AtomRegistry:
    """Get global atom registry instance."""
    global _atom_registry
    if _atom_registry is None:
        _atom_registry = AtomRegistry()
    return _atom_registry
