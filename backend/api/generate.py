from fastapi import APIRouter
from pydantic import BaseModel
from backend.core.orchestrator import run_agents

router = APIRouter(prefix="/generate", tags=["Project Generator"])

class ProjectRequest(BaseModel):
    idea: str

@router.post("/project")
def generate_project(req: ProjectRequest):
    result = run_agents(req.idea)
    return {
        "message": "Project generated successfully",
        "data": result
    }
