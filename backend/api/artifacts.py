"""
Artifacts API - File tree and generated outputs.
MetaGPT-style: Track what was created.
"""

import hashlib
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.user import User
from backend.models.project import Project
from backend.models.artifact import Artifact, ArtifactType

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])

MAX_SYNC_FILES = 2000
MAX_FILE_BYTES = 2 * 1024 * 1024  # 2MB per file payload


class ArtifactSyncRequest(BaseModel):
    files: Dict[str, str] = Field(default_factory=dict)
    run_id: Optional[int] = None
    replace_existing: bool = True


def _normalize_artifact_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip().lstrip("/")
    if not normalized:
        raise ValueError("Empty artifact path")

    parts = [part for part in normalized.split("/") if part and part != "."]
    if any(part == ".." for part in parts):
        raise ValueError("Path traversal is not allowed")

    return "/".join(parts)


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


@router.post("/{project_id}/sync")
def sync_artifacts(
    project_id: str,
    payload: ArtifactSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Persist generated project files into DB artifacts.

    Frontend uses this after generation so project files are saved in DB
    (instead of being only on local disk preview folders).
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if len(payload.files) > MAX_SYNC_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Max allowed is {MAX_SYNC_FILES}.",
        )

    try:
        if payload.replace_existing:
            db.query(Artifact).filter(Artifact.project_id == project_id).delete(synchronize_session=False)

        saved = 0
        skipped_invalid_path = 0
        skipped_too_large = 0

        for raw_path, content in payload.files.items():
            try:
                artifact_path = _normalize_artifact_path(raw_path)
            except ValueError:
                skipped_invalid_path += 1
                continue

            if not isinstance(content, str):
                content = str(content)

            encoded = content.encode("utf-8")
            if len(encoded) > MAX_FILE_BYTES:
                skipped_too_large += 1
                continue

            db.add(
                Artifact(
                    project_id=project_id,
                    run_id=payload.run_id,
                    name=artifact_path.split("/")[-1],
                    path=artifact_path,
                    artifact_type=ArtifactType.FILE.value,
                    file_size=len(encoded),
                    content_hash=hashlib.sha256(encoded).hexdigest(),
                    # Store full file text in DB for project restore.
                    description=content,
                )
            )
            saved += 1

        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to sync artifacts")

    return {
        "project_id": project_id,
        "saved": saved,
        "skipped_invalid_path": skipped_invalid_path,
        "skipped_too_large": skipped_too_large,
        "replace_existing": payload.replace_existing,
    }


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


@router.get("/{project_id}/content")
def get_artifact_content(
    project_id: str,
    path: str,
    run_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single artifact's file content by path."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        normalized_path = _normalize_artifact_path(path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    query = db.query(Artifact).filter(
        Artifact.project_id == project_id,
        Artifact.path == normalized_path,
    )
    if run_id:
        query = query.filter(Artifact.run_id == run_id)

    artifact = query.order_by(Artifact.id.desc()).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return {
        "id": artifact.id,
        "path": artifact.path,
        "content": artifact.description or "",
        "file_size": artifact.file_size,
        "updated_at": artifact.updated_at,
    }
