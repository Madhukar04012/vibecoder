# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

VibeCober is an AI-powered project generator that transforms ideas into production-ready code using a multi-agent pipeline. It has two execution modes:

1. **CLI Pipeline** (`cli.py` → `backend/core/orchestrator.py`): Generates standalone projects via command line
2. **Atoms Engine** (`backend/engine/atoms_engine.py`): Web-based execution with state machine, token ledger, and QA gates

## Build & Run Commands

```bash
# Backend (FastAPI)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (Vite + React)
cd frontend && npm run dev

# Install dependencies
pip install -r backend/requirements.txt
cd frontend && npm install

# Windows launchers available: start.bat, start-backend.bat, start-frontend.bat
```

## Testing

```bash
# Backend (pytest)
pytest backend/tests/
pytest backend/tests/test_circuit_breaker.py -v    # Single test file

# Frontend (vitest)
cd frontend && npm test                             # Run once
cd frontend && npm run test:watch                   # Watch mode

# Type checking (frontend)
cd frontend && npm run typecheck
```

## CLI Usage

```bash
# Generate project (preview mode)
python cli.py generate "todo app" --simple

# Generate with files (production-ready)
python cli.py generate "SaaS with auth" --production --build --output ./my-project

# Modes: --simple (planner+coder), --full (default), --production (all 7 agents)
# Flags: --build (write files), --skip-tests, --no-docker, --v1 (legacy pipeline)
```

## Architecture

### Agent Pipeline (orchestrator)

```
User Idea → Team Lead Brain (decide agents) → Orchestrator (execute) → Generated Project
```

**Agent execution order** (dependencies respected):
- `planner` → `db_schema` → `auth` → `coder` → `code_reviewer` → `tester` → `deployer`

Agents are in `backend/agents/`. The Team Lead Brain (`team_lead_brain.py`) is deterministic (keyword-based analysis, no AI calls).

### Atoms Engine (web UI)

The Atoms Engine (`backend/engine/`) orchestrates web-based generation with:
- **State machine** (`state.py`): IDLE → PLANNING → APPROVED → EXECUTION → QA
- **Token ledger** (`token_ledger.py`): Cost tracking per agent with budget enforcement
- **Circuit breaker** (`circuit_breaker.py`): Blocks execution on repeated QA failures
- **Event system** (`events.py`): Emits events for UI updates

### Backend Structure

- `backend/main.py` — FastAPI app entry point, CORS, all routers
- `backend/api/` — HTTP routers (auth, projects, generate, agents, chat_stream, terminal_ws, etc.)
- `backend/agents/` — All agent implementations
- `backend/engine/` — Atoms engine, state machine, LLM gateway, sandbox, HITL
- `backend/models/` — SQLAlchemy models (User, Project, Task, Agent, ProjectRun, Artifact)
- `backend/memory/` — FAISS indexer and retriever for semantic memory

### Frontend Structure

- `frontend/src/main.tsx` — React root with providers
- `frontend/src/router.tsx` — Routes: `/` (landing), `/login`, `/signup`, `/ide` (NovaIDE), `/dashboard`
- `frontend/src/components/NovaIDE.tsx` — Main IDE shell (see UI rules below)
- `frontend/src/stores/ide-store.ts` — Zustand store for IDE state
- `frontend/src/lib/api.ts` — API fetch wrapper

## Critical Rules

### NovaIDE UI is FROZEN

The NovaIDE component matches Atoms pixel-for-pixel. When modifying `NovaIDE.tsx` or `atoms-ide-layout.css`:

- **Use CSS variables** from `atoms-ide-layout.css` for all layout values
- **Do NOT add**: onboarding copy, tooltips, helper text, animations, fade-ins, "smart" empty states
- **Allowed text only**: "NOVA AI Assistant", "Editor", "App" (top bar), "Ask AI…" (sidebar placeholder), "Select a file" (empty editor)
- **Changes allowed**: functionality inside shell, bug fixes preserving visual parity, accessibility (aria-labels)

### Environment Variables

Copy `.env.example` to `.env`. Key variables:
- `DATABASE_URL` — PostgreSQL connection (Railway injects automatically)
- `JWT_SECRET_KEY` — Must change in production
- `NIM_API_KEY`, `NIM_MODEL` — NVIDIA NIM API for DeepSeek reasoning

## Database

- Development uses SQLite (`vibecober.db`)
- Production uses PostgreSQL
- Alembic migrations in `backend/migrations/`
- Run `python check_db.py` to verify DB and create default user
