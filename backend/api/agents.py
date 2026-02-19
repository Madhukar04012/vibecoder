"""
Agents API - Endpoints to trigger and control AI agents.
Enables direct agent execution via API.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.project import Project
from backend.models.user import User
from backend.agents.backend_engineer import BackendEngineerAgent
from backend.agents.frontend_engineer import FrontendEngineerAgent

router = APIRouter(prefix="/agents", tags=["Agents"])


# ============ BACKEND AGENT ============

@router.post("/backend/{project_id}/run")
def run_backend_agent(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run Backend Engineer Agent on next available task."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    agent = BackendEngineerAgent(db)
    result = agent.run_next_task(project_id)

    return {
        "project_id": project_id,
        "agent": "backend_engineer",
        "result": result,
    }


@router.post("/backend/{project_id}/run-all")
def run_all_backend_tasks(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run Backend Engineer Agent on ALL pending tasks."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    agent = BackendEngineerAgent(db)
    results = []
    
    while True:
        result = agent.run_next_task(project_id)
        if result["status"] == "no_tasks":
            break
        results.append(result)
        if result["status"] == "failed":
            break

    return {
        "project_id": project_id,
        "agent": "backend_engineer",
        "tasks_completed": len([r for r in results if r["status"] == "completed"]),
        "tasks_failed": len([r for r in results if r["status"] == "failed"]),
        "results": results,
    }


# ============ FRONTEND AGENT ============

@router.post("/frontend/{project_id}/run")
def run_frontend_agent(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run Frontend Engineer Agent on next available task."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    agent = FrontendEngineerAgent(db)
    result = agent.run_next_task(project_id)

    return {
        "project_id": project_id,
        "agent": "frontend_engineer",
        "result": result,
    }


@router.post("/frontend/{project_id}/run-all")
def run_all_frontend_tasks(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run Frontend Engineer Agent on ALL pending tasks."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    agent = FrontendEngineerAgent(db)
    results = []
    
    while True:
        result = agent.run_next_task(project_id)
        if result["status"] == "no_tasks":
            break
        results.append(result)
        if result["status"] == "failed":
            break

    return {
        "project_id": project_id,
        "agent": "frontend_engineer",
        "tasks_completed": len([r for r in results if r["status"] == "completed"]),
        "tasks_failed": len([r for r in results if r["status"] == "failed"]),
        "results": results,
    }

