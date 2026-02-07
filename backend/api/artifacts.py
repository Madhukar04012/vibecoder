"""
Artifacts API - File tree and generated outputs.
MetaGPT-style: Track what was created.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.user import User
from backend.models.project import Project
from backend.models.artifact import Artifact

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.get("/{project_id}")
def get_artifacts(
    project_id: str,
    run_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all artifacts for a project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    query = db.query(Artifact).filter(Artifact.project_id == project_id)
    
    if run_id:
        query = query.filter(Artifact.run_id == run_id)
    
    artifacts = query.order_by(Artifact.path).all()
    
    return [
        {
            "id": artifact.id,
            "name": artifact.name,
            "path": artifact.path,
            "type": artifact.artifact_type,
            "file_size": artifact.file_size,
            "created_at": artifact.created_at
        }
        for artifact in artifacts
    ]


@router.get("/{project_id}/tree")
def get_file_tree(
    project_id: str,
    run_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get artifacts as a file tree structure."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    query = db.query(Artifact).filter(Artifact.project_id == project_id)
    
    if run_id:
        query = query.filter(Artifact.run_id == run_id)
    
    artifacts = query.order_by(Artifact.path).all()
    
    # Build tree structure
    tree = {}
    for artifact in artifacts:
        parts = artifact.path.split("/")
        current = tree
        for i, part in enumerate(parts):
            if part not in current:
                is_file = (i == len(parts) - 1) and artifact.artifact_type == "file"
                current[part] = {
                    "_name": part,
                    "_type": "file" if is_file else "folder",
                    "_id": artifact.id if is_file else None
                }
            current = current[part]
    
    return tree
