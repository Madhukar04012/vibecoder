"""
Task API Routes - CRUD and control operations for tasks
Supports: list by project, update status, assign agent
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.task import Task
from backend.models.project import Project
from backend.models.user import User
from backend.schemas.task import (
    TaskRead,
    TaskUpdateStatus,
    TaskAssignAgent,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/projects/{project_id}", response_model=List[TaskRead])
def list_project_tasks(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all tasks for a specific project.
    Requires project ownership.
    """
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project.tasks


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific task by ID.
    Requires ownership of the parent project.
    """
    task = (
        db.query(Task)
        .join(Project)
        .filter(Task.id == task_id, Project.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.patch("/{task_id}/status", response_model=TaskRead)
def update_task_status(
    task_id: int,
    payload: TaskUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the status of a task.
    Valid statuses: todo, in_progress, done
    """
    task = (
        db.query(Task)
        .join(Project)
        .filter(Task.id == task_id, Project.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = payload.status
    db.commit()
    db.refresh(task)

    return task


@router.patch("/{task_id}/assign", response_model=TaskRead)
def assign_task_agent(
    task_id: int,
    payload: TaskAssignAgent,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assign an agent to a task.
    Valid agents: team_lead, backend_engineer, frontend_engineer, database_engineer, qa_engineer
    """
    task = (
        db.query(Task)
        .join(Project)
        .filter(Task.id == task_id, Project.user_id == current_user.id)
        .first()
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.assigned_agent = payload.assigned_agent
    db.commit()
    db.refresh(task)

    return task
