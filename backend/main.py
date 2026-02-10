"""
VibeCober API - Main Application
v0.6.1: MetaGPT-style architecture with Agents, Runs, Messages, Artifacts
+ Phase-2: Environment & Visualization (Terminal WS, Events)
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging

from backend.database import Base, engine
from backend.api import auth, projects, team_lead, tasks, agents, logs
from backend.api.generate import router as generate_router
from backend.api import runs, messages, artifacts
from backend.api.studio import router as studio_router
from backend.api.metagpt_engine import router as metagpt_router
from backend.api.chat_stream import router as chat_stream_router
from backend.api.chat_simple import router as chat_router
from backend.api.run import router as run_router
from backend.api.atoms_engine import router as atoms_router
from backend.api.terminal_ws import router as terminal_router
from backend.api.hitl import router as hitl_router
from backend.api.marketplace import router as marketplace_router
from backend.api.snapshot import router as snapshot_router
from backend.api.atmos import router as atmos_router

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
    version="0.7.0"
)

# CORS middleware - allow all origins for local dev (browser fetch from any port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Required when using allow_origins=["*"]
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

# Include MetaGPT engine router
app.include_router(metagpt_router)

# Chat streaming (Replit-style live typing)
app.include_router(chat_stream_router)

# Simple chat (connectivity verification)
app.include_router(chat_router, prefix="/api")

# Code execution (Phase 3)
app.include_router(run_router)

# Atoms Engine (Multi-Agent + Race Mode)
app.include_router(atoms_router)

# Phase-2: Terminal WebSocket
app.include_router(terminal_router)

# Phase-4: HITL Clarification Cards
app.include_router(hitl_router)

# Phase-6: Atoms Marketplace
app.include_router(marketplace_router)

# Phase-5: Time-Travel Snapshots
app.include_router(snapshot_router)

# ATMOS: AI-Only Autonomous Pipeline
app.include_router(atmos_router)


# ---------- Global exception handler ----------

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/api/status")
def api_status():
    return {"status": "VibeCober API running", "version": "0.7.0"}


@app.get("/api/circuit-breakers")
def circuit_breaker_status():
    """Get status of all circuit breakers."""
    from backend.engine.circuit_breaker import get_all_breaker_statuses
    return {"breakers": get_all_breaker_statuses()}


@app.get("/api/race-mode/history")
def race_mode_history():
    """Get race mode execution history."""
    from backend.engine.race_mode import get_race_mode
    return {"races": get_race_mode().get_history()}


@app.get("/api/prompt-optimizer/stats")
def optimizer_stats():
    """Get prompt optimizer statistics."""
    from backend.engine.prompt_optimizer import get_prompt_optimizer
    return {"stats": get_prompt_optimizer().get_stats()}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---------- Serve frontend (single-server mode) ----------

_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


def _serve_spa(path: str = ""):
    index_path = _FRONTEND_DIST / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse(content={"error": "Frontend not built. Run: cd frontend && npm run build"}, status_code=503)


if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa_route(full_path: str):
        if full_path and not full_path.startswith("assets/"):
            file_path = _FRONTEND_DIST / full_path
            if file_path.is_file():
                return FileResponse(file_path)
        return _serve_spa(full_path)
