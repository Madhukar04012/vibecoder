"""
VibeCober API - Main Application
v0.6.0: MetaGPT-style architecture with Agents, Runs, Messages, Artifacts
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from backend.database import Base, engine
from backend.api import auth, projects, team_lead, tasks, agents, logs
from backend.api.generate import router as generate_router
from backend.api import runs, messages, artifacts
from backend.api.studio import router as studio_router

# Import all models to ensure they're registered
from backend.models import (
    User, Project, ProjectAgent, ProjectPlan, Conversation, Task, ExecutionLog,
    Agent, AgentMessage, ProjectRun, Artifact
)

logger = logging.getLogger("vibecober")

# Create all database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="VibeCober API",
    description="AI-powered project generator with multi-agent architecture (MetaGPT-style)",
    version="0.6.1"
)

# CORS middleware - explicit origins required when credentials=True (wildcard invalid)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (original)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(team_lead.router)
app.include_router(tasks.router)
app.include_router(agents.router)
app.include_router(logs.router)
app.include_router(generate_router)

# Include routers (MetaGPT-style)
app.include_router(runs.router)
app.include_router(messages.router)
app.include_router(artifacts.router)

# Include studio router (IDE + workspace API)
app.include_router(studio_router)


# ---------- Global exception handler ----------

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
def root():
    return {
        "status": "VibeCober API running",
        "version": "0.6.1",
        "phase": "MetaGPT-style Architecture"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
