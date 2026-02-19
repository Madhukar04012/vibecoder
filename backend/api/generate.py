import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.core.pipeline_runner import PipelineRequest, run_pipeline
from backend.schemas.project import MAX_IDEA_LEN

router = APIRouter(prefix="/generate", tags=["Project Generator"])
logger = logging.getLogger(__name__)

MAX_MODE_LEN = 32


class ProjectRequest(BaseModel):
    idea: str = Field(..., min_length=1, max_length=MAX_IDEA_LEN)
    mode: str = Field("full", max_length=MAX_MODE_LEN)  # simple, full, or production
    token_tier: str = Field("free", max_length=16)
    project_id: str | None = Field(None, max_length=128)
    memory_scope: str = Field("project", max_length=16)


@router.post("/project")
def generate_project(req: ProjectRequest):
    """Generate project using Team Lead Brain (Phase 2)."""
    try:
        request = PipelineRequest(
            idea=req.idea,
            mode=req.mode,
            channel="api",
            user_id="anonymous-api",
            project_id=req.project_id,
            token_tier=req.token_tier,
            memory_scope=req.memory_scope,
        )
        result = run_pipeline(request)
        return {
            "message": "Project generated successfully",
            "data": result,
        }
    except Exception as e:
        logger.exception("Project generation failed: idea=%s", req.idea[:100])
        raise HTTPException(status_code=500, detail="Project generation failed. Check server logs.") from e
