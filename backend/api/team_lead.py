"""
Team Lead API - Endpoints for chatting with the AI
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.team_lead import IdeaInput, TeamLeadResponse, PlanApproval
from backend.agents.team_lead import TeamLeadAgent
from backend.models.conversation import Conversation
from backend.models.project import Project

router = APIRouter(prefix="/team-lead", tags=["Team Lead"])


@router.post("/{project_id}/start", response_model=TeamLeadResponse)
def start_conversation(
    project_id: str,
    idea_input: IdeaInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start/Continue conversation with Team Lead.
    Handles idea input -> decides Questions vs Plan.
    """
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    agent = TeamLeadAgent(project_id, db)
    response = agent.process_input(idea_input.idea)
    
    # If plan generated, save it
    if response.type == "plan" and response.plan:
        agent.save_plan(response.plan)
        
    return response


@router.post("/{project_id}/approve")
def approve_plan(
    project_id: str,
    approval: PlanApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve or reject the project plan.
    On approval: auto-generates tasks via TaskManagerAgent.
    """
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    from backend.models.project_plan import ProjectPlan
    plan = db.query(ProjectPlan).filter(ProjectPlan.project_id == project_id).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No plan found")

    if approval.approved:
        # Safety check: prevent double approval
        if plan.approved:
            return {
                "status": "already_approved",
                "message": "Plan already approved. Tasks already generated."
            }
        
        # 1. Mark plan as approved
        plan.approved = True
        
        # 2. Auto-generate tasks via TaskManagerAgent
        from backend.agents.task_manager import TaskManagerAgent
        task_manager = TaskManagerAgent(db)
        tasks = task_manager.run(project_id=project.id, plan=plan)
        
        # 3. Move project into BUILDING phase
        project.status = "building"
        
        db.commit()
        
        return {
            "status": "approved",
            "next_phase": "building",
            "tasks_created": len(tasks),
            "message": f"Plan approved. {len(tasks)} tasks auto-generated."
        }
    else:
        # If rejected, loop back for revision
        return {"status": "rejected", "message": "Feedback received. Plan needs revision."}

