# VibeCober — Project Structure

High-level map for developers. Entry points: **Backend** `backend/main.py`, **Frontend** `frontend/src/main.tsx`, **CLI** `cli.py`.

---

## Root

| Item | Purpose |
|------|--------|
| `cli.py` | CLI: `generate`, `run backend/frontend/all`, `logs` |
| `run_backend.py` | Starts uvicorn (backend) |
| `check_db.py` | DB check + create default user |
| `start.bat` / `start-backend.bat` / `start-frontend.bat` | Windows launchers |
| `.env.example` | Env template (copy to `.env`) |

---

## Backend (`backend/`)

| Path | Purpose |
|------|--------|
| **main.py** | FastAPI app, CORS, all routers, static SPA serve |
| **database.py** | SQLAlchemy engine, Base, SessionLocal, get_db |
| **api/** | HTTP routers: auth, projects, team_lead, tasks, agents, logs, generate, runs, messages, artifacts, studio, metagpt_engine, chat_stream, chat_simple, run, atoms_engine, terminal_ws, hitl, marketplace, snapshot, atmos |
| **auth/** | JWT, dependencies (get_current_user), security (hash/verify password) |
| **models/** | SQLAlchemy models (User, Project, Task, Agent, ProjectRun, Artifact, etc.) |
| **schemas/** | Pydantic schemas (user, project, task, team_lead) |
| **agents/** | Planner, DB schema, Auth, Coder, Tester, Deploy, Team Lead, Task Manager, Backend/Frontend Engineer, Product Manager, Architect, Engineer, QA Tester, Judge (orchestrator vs atoms engine) |
| **core/** | Orchestrator (CLI pipeline), agent_registry, llm_client |
| **engine/** | Atoms engine, state, events, sandbox, LLM gateway, token ledger, circuit breaker, race mode, HITL, snapshot, fleet, atom_loader, prompt_optimizer, self_healer, planning_validator |
| **memory/** | Indexer (FAISS), retriever — used by atoms engine |
| **marketplace/** | Atom manifest, registry |
| **services/** | Deployment, diff engine, testing |
| **tools/** | Shell executor, MCP manager |
| **communication/** | Presence, sync engine (events) |
| **generator/** | project_builder (merge agent outputs) |
| **migrations/** | Alembic |
| **tests/** | Pytest: circuit_breaker, sandbox, snapshot_manager, budget_enforcement |

---

## Frontend (`frontend/`)

| Path | Purpose |
|------|--------|
| **src/main.tsx** | React root: SettingsProvider, ErrorBoundary, RouterProvider |
| **src/router.tsx** | Routes: `/` VibeCober, `/login`, `/signup`, `/ide` NovaIDE, `/dashboard`; auth gates |
| **src/pages/** | Login, Signup, Dashboard |
| **src/components/** | NovaIDE (IDE shell), AtomsTopBar, AtomsChatPanel, FilePanel, EditorPanel, EditorCanvas, EditorTabs, VibeCober (landing), SettingsPanel, ChatTopBar, AccountHoverPanel, ErrorBoundary, animated-auth-layout |
| **src/components/ui/** | Radix-based: button, card, input, dialog, select, switch, avatar, etc. |
| **src/contexts/** | AuthContext, SettingsContext, ThemeContext |
| **src/stores/** | ide-store (Zustand) |
| **src/lib/** | api.ts (apiFetch, getApiUrl), atmos-state, event-bus, utils (cn) |
| **src/api/** | auth.ts (login, signup, getMe) |
| **src/utils/** | settings.ts (getCurrentModel, onModelChange, etc.) |
| **src/examples/** | Reference only (see SETTINGS_DOCUMENTATION.md) |
| **atoms-chat.css / atoms-ide-layout.css** | Imported by index.css |

---

## What Was Removed (Cleanup)

- **backend/memory/distributed_memory.py** — Redis-backed distributed memory; not referenced anywhere.
- **backend/storage/vector_cache.py** — Redis-backed embedding cache; not referenced anywhere.
- **frontend/src/lib/monaco-atoms-theme.ts** — Monaco theme/options; editor uses inline `vs-dark` and options.
- **backend/storage/snapshot_manager.py** — Legacy snapshot manager; replaced by `backend/engine/snapshot_manager.py`.

---

## Run Order

1. Backend: `python run_backend.py` or `uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`
2. Frontend: `cd frontend && npm run dev`
3. Optional: `python check_db.py` to ensure DB and default user.
