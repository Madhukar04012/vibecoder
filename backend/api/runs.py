"""
Project Runs API - Endpoints for managing build sessions.
MetaGPT-style: Runs are first-class entities.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.user import User
from backend.models.project import Project
from backend.models.project_run import ProjectRun, RunStatus
from backend.models.agent import Agent, AgentStatus
from backend.models.agent_message import AgentMessage, MessageType, SenderType
from backend.models.enums import AgentRole

router = APIRouter(prefix="/runs", tags=["Project Runs"])


@router.get("/{project_id}")
def list_runs(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all runs for a project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    runs = db.query(ProjectRun).filter(
        ProjectRun.project_id == project_id
    ).order_by(ProjectRun.created_at.desc()).all()
    
    return [
        {
            "id": run.id,
            "status": run.status,
            "triggered_by": run.triggered_by,
            "tasks_completed": run.tasks_completed,
            "tasks_failed": run.tasks_failed,
            "files_created": run.files_created,
            "started_at": run.started_at,
            "finished_at": run.finished_at
        }
        for run in runs
    ]


@router.get("/{project_id}/{run_id}")
def get_run(
    project_id: str,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific run with details."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    run = db.query(ProjectRun).filter(
        ProjectRun.id == run_id,
        ProjectRun.project_id == project_id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {
        "id": run.id,
        "project_id": run.project_id,
        "status": run.status,
        "triggered_by": run.triggered_by,
        "tasks_completed": run.tasks_completed,
        "tasks_failed": run.tasks_failed,
        "files_created": run.files_created,
        "error_message": run.error_message,
        "started_at": run.started_at,
        "finished_at": run.finished_at
    }


@router.post("/{project_id}/start")
def start_run(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new build run for a project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if already running
    existing_run = db.query(ProjectRun).filter(
        ProjectRun.project_id == project_id,
        ProjectRun.status == RunStatus.RUNNING
    ).first()
    
    if existing_run:
        raise HTTPException(status_code=400, detail="A run is already in progress")
    
    # Create new run
    run = ProjectRun(
        project_id=project_id,
        status=RunStatus.RUNNING,
        triggered_by="user"
    )
    db.add(run)
    
    # Initialize agents for this project if not exists
    _ensure_agents_exist(db, project_id)
    
    # Update agent statuses
    agents = db.query(Agent).filter(Agent.project_id == project_id).all()
    for agent in agents:
        agent.status = AgentStatus.IDLE
    
    # Add system message
    msg = AgentMessage(
        project_id=project_id,
        sender=SenderType.SYSTEM,
        message_type=MessageType.SYSTEM,
        content=f"Build run #{run.id} started"
    )
    db.add(msg)
    
    db.commit()
    db.refresh(run)
    
    return {
        "run_id": run.id,
        "status": run.status,
        "message": "Build run started"
    }


def _ensure_agents_exist(db: Session, project_id: str):
    """Create default agents for a project if they don't exist."""
    existing = db.query(Agent).filter(Agent.project_id == project_id).count()
    
    if existing == 0:
        default_agents = [
            {"name": "Team Lead", "role": AgentRole.TEAM_LEAD, "description": "Plans architecture and coordinates team"},
            {"name": "Backend Engineer", "role": AgentRole.BACKEND_ENGINEER, "description": "Builds FastAPI backend"},
            {"name": "Frontend Engineer", "role": AgentRole.FRONTEND_ENGINEER, "description": "Builds React frontend"},
            {"name": "Database Engineer", "role": AgentRole.DATABASE_ENGINEER, "description": "Designs and manages database"},
            {"name": "QA Engineer", "role": AgentRole.QA_ENGINEER, "description": "Tests and validates code"},
        ]
        
        for agent_data in default_agents:
            agent = Agent(
                project_id=project_id,
                name=agent_data["name"],
                role=agent_data["role"],
                description=agent_data["description"],
                status=AgentStatus.IDLE
            )
            db.add(agent)
