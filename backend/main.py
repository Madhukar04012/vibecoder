"""
VibeCober API - Main Application
v0.6.1: MetaGPT-style architecture with Agents, Runs, Messages, Artifacts
+ Phase-2: Environment & Visualization (Terminal WS, Events)
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.auth.dependencies import get_current_user

# Configure structured logging
_env = os.getenv("ENV", "development").lower()
_structured_logging = _env == "production"

if _structured_logging:
    # JSON structured logging for production
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
        force=True,
    )
else:
    # Human-readable logging for development
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
        force=True,
    )

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
from backend.api.pipeline_governance import router as pipeline_governance_router
from backend.api.agent_chat import router as agent_chat_router
from backend.api.society import router as society_router
from backend.api.nim_ws import router as nim_ws_router
from backend.api.nim_test import router as nim_test_router

# Import all models to ensure they're registered
from backend.models import (
    User, Project, ProjectAgent, ProjectPlan, Conversation, Task, ExecutionLog,
    Agent, AgentMessage, ProjectRun, Artifact,
    NimProject, NimDagSnapshot, NimTask, NimTaskOutput, NimAgentLog,
)

logger = logging.getLogger("vibecober")


def _validate_env() -> None:
    """Validate required environment variables on startup. Fail fast in production."""
    env = os.getenv("ENV", "development").lower()
    if env == "production":
        required = ["DATABASE_URL", "JWT_SECRET_KEY"]
        missing = [k for k in required if not os.getenv(k) or not str(os.getenv(k)).strip()]
        if missing:
            raise RuntimeError(
                f"Production requires these environment variables: {', '.join(missing)}. "
                "Set them in .env or the deployment environment."
            )
        secret = os.getenv("JWT_SECRET_KEY", "")
        if secret in ("", "vibecober-dev-secret-change-in-production"):
            raise RuntimeError(
                "JWT_SECRET_KEY must be set to a strong secret in production. "
                "Do not use the default dev value."
            )
    else:
        if not os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY") == "your-super-secret-key-change-in-production":
            logger.warning(
                "JWT_SECRET_KEY is default or missing. Use a strong secret in production."
            )


# Initialize database tables
# Try to run migrations first, fall back to create_all if migrations unavailable
try:
    from backend.migrate_db import run_migrations
    migrations_successful = run_migrations()
    if not migrations_successful:
        logger.info("Using create_all as fallback")
except Exception as e:
    logger.warning(f"Migrations unavailable, using create_all: {e}")
    Base.metadata.create_all(bind=engine)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute", "1000/hour"])

@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Lifespan: validate env on startup; no shutdown work required."""
    _validate_env()
    yield


# Initialize FastAPI app
app = FastAPI(
    title="VibeCober API",
    description="AI-powered project generator with multi-agent architecture (MetaGPT-style)",
    version="0.7.0",
    lifespan=_lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: set CORS_ORIGINS in production (e.g. "https://app.example.com")
# Default: allow localhost in development only
_env = os.getenv("ENV", "development").lower()
_cors_origins = os.getenv("CORS_ORIGINS", "").strip()

if _cors_origins:
    # User explicitly set CORS_ORIGINS
    _cors_list = [o.strip() for o in _cors_origins.split(",") if o.strip()]
elif _env == "production":
    # Production: require explicit configuration, fail-safe to empty
    logger.warning("Production mode requires CORS_ORIGINS to be set. Using empty list (no CORS).")
    _cors_list = []
else:
    # Development: allow localhost variants
    _cors_list = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:3000",
    ]
    logger.info(f"Development mode: allowing CORS from localhost: {_cors_list}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
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

# Unified Pipeline Governance
app.include_router(pipeline_governance_router)

# Agent Chat Proxy (secure Anthropic API access)
app.include_router(agent_chat_router)
app.include_router(society_router)

# NIM Multi-Agent System — Phase 4: WebSocket streaming
app.include_router(nim_ws_router)

# NIM Multi-Agent System — Model connectivity test + config
app.include_router(nim_test_router)


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
def circuit_breaker_status(current_user: User = Depends(get_current_user)):
    """Get status of all circuit breakers (auth required)."""
    from backend.engine.circuit_breaker import get_all_breaker_statuses
    return {"breakers": get_all_breaker_statuses()}


@app.get("/api/race-mode/history")
def race_mode_history(current_user: User = Depends(get_current_user)):
    """Get race mode execution history (auth required)."""
    from backend.engine.race_mode import get_race_mode
    return {"races": get_race_mode().get_history()}


@app.get("/api/prompt-optimizer/stats")
def optimizer_stats(current_user: User = Depends(get_current_user)):
    """Get prompt optimizer statistics (auth required)."""
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
