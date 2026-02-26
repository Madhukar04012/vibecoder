"""
Marketplace API — Phase 6

API endpoints for Atoms Marketplace.

Endpoints:
- GET /api/marketplace/installed - List installed atoms
- POST /api/marketplace/install - Install an atom
- DELETE /api/marketplace/{atom_id} - Uninstall atom
- POST /api/marketplace/{atom_id}/enable - Enable atom
- POST /api/marketplace/{atom_id}/disable - Disable atom
- GET /api/marketplace/{atom_id} - Get atom details
"""

import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.marketplace.registry import get_atom_registry
from backend.engine.atom_loader import get_atom_loader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

# Atoms must be installed from within the project directory tree
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ─── Request Models ──────────────────────────────────────────────────────────

class InstallRequest(BaseModel):
    source_path: str = Field(..., max_length=500)
    approved_by: str = "user"


class AtomActionRequest(BaseModel):
    atom_id: str


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/installed")
async def list_installed():
    """List all installed atoms."""
    registry = get_atom_registry()
    return {
        "atoms": registry.list_installed(),
        "count": len(registry.atoms),
    }


@router.post("/install")
async def install_atom(request: InstallRequest):
    """Install an atom from source path (must be within project tree)."""
    registry = get_atom_registry()

    source = Path(request.source_path).resolve()

    # Security: block path traversal — source must be inside project root
    try:
        source.relative_to(_PROJECT_ROOT)
    except ValueError:
        logger.warning("Marketplace install blocked — path outside project: %s", request.source_path[:200])
        raise HTTPException(
            status_code=400,
            detail="Source path must be within the project directory.",
        )

    if not source.exists():
        raise HTTPException(status_code=404, detail="Source path not found.")

    if not (source / "atom.yaml").exists():
        raise HTTPException(status_code=400, detail="No atom.yaml found in source path.")

    try:
        installed = registry.install(
            str(source),
            approved_by=request.approved_by,
        )
        return {
            "status": "installed",
            "atom": installed.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OSError as e:
        logger.error("Atom install failed: %s", e)
        raise HTTPException(status_code=500, detail="Install failed due to filesystem error.")


@router.delete("/{atom_id}")
async def uninstall_atom(atom_id: str):
    """Uninstall an atom."""
    registry = get_atom_registry()
    loader = get_atom_loader()
    
    # Unload if running
    loader.unload_atom(atom_id)
    
    if registry.uninstall(atom_id):
        return {"status": "uninstalled", "atom_id": atom_id}
    
    raise HTTPException(status_code=404, detail=f"Atom not found: {atom_id}")


@router.post("/{atom_id}/enable")
async def enable_atom(atom_id: str):
    """Enable an installed atom."""
    registry = get_atom_registry()
    
    if registry.enable(atom_id):
        return {"status": "enabled", "atom_id": atom_id}
    
    raise HTTPException(status_code=404, detail=f"Atom not found: {atom_id}")


@router.post("/{atom_id}/disable")
async def disable_atom(atom_id: str):
    """Disable an installed atom."""
    registry = get_atom_registry()
    loader = get_atom_loader()
    
    # Unload if running
    loader.unload_atom(atom_id)
    
    if registry.disable(atom_id):
        return {"status": "disabled", "atom_id": atom_id}
    
    raise HTTPException(status_code=404, detail=f"Atom not found: {atom_id}")


@router.get("/{atom_id}")
async def get_atom(atom_id: str):
    """Get atom details."""
    registry = get_atom_registry()
    
    atom = registry.get(atom_id)
    if atom:
        return {"atom": atom.to_dict()}
    
    raise HTTPException(status_code=404, detail=f"Atom not found: {atom_id}")


@router.post("/{atom_id}/load")
async def load_atom(atom_id: str):
    """Load atom into memory for execution."""
    registry = get_atom_registry()
    loader = get_atom_loader()
    
    atom = registry.get(atom_id)
    if not atom:
        raise HTTPException(status_code=404, detail=f"Atom not found: {atom_id}")
    
    if not atom.enabled:
        raise HTTPException(status_code=400, detail=f"Atom is disabled: {atom_id}")
    
    try:
        instance = loader.load_atom(atom.install_path, atom.manifest)
        return {
            "status": "loaded",
            "atom_id": atom_id,
            "wasm_support": loader.has_wasm_support,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Load failed: {e}")


@router.post("/{atom_id}/run")
async def run_atom(atom_id: str, context: Optional[dict] = None):
    """Execute an atom's main function."""
    loader = get_atom_loader()
    
    instance = loader.get_instance(atom_id)
    if not instance:
        # Try to load first
        registry = get_atom_registry()
        atom = registry.get(atom_id)
        if not atom:
            raise HTTPException(status_code=404, detail=f"Atom not found: {atom_id}")
        instance = loader.load_atom(atom.install_path, atom.manifest)
    
    result = instance.run(context or {})
    return {"result": result}
