"""
Agent Messages API - Timeline & conversation endpoints.
MetaGPT-style: Agent thoughts and actions as a stream.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.user import User
from backend.models.project import Project
from backend.models.agent import Agent
from backend.models.agent_message import AgentMessage, MessageType, SenderType

router = APIRouter(prefix="/messages", tags=["Agent Messages"])


@router.get("/{project_id}")
def get_messages(
    project_id: str,
    limit: int = 50,
    run_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get message timeline for a project.
    This is the main feed for the MetaGPT-style UI.
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    query = db.query(AgentMessage).filter(AgentMessage.project_id == project_id)
    
    if run_id:
        query = query.filter(AgentMessage.run_id == run_id)
    if agent_id:
        query = query.filter(AgentMessage.agent_id == agent_id)
    
    messages = query.order_by(AgentMessage.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": msg.id,
            "agent_id": msg.agent_id,
            "sender": msg.sender.value if msg.sender else None,
            "message_type": msg.message_type.value if msg.message_type else None,
            "content": msg.content,
            "created_at": msg.created_at
        }
        for msg in reversed(messages)  # Return in chronological order
    ]


@router.get("/{project_id}/agents")
def get_agents(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all agents for a project with their current status."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    agents = db.query(Agent).filter(Agent.project_id == project_id).all()
    
    return [
        {
            "id": agent.id,
            "name": agent.name,
            "role": agent.role.value if agent.role else None,
            "status": agent.status,
            "description": agent.description,
            "last_active_at": agent.last_active_at
        }
        for agent in agents
    ]
