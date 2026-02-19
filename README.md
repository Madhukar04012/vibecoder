# VibeCober

## AI-Powered Project Generator & Agentic Software Factory

Transform a single idea into a production-ready codebase using a multi-agent pipeline with real-time IDE, WebSocket progress streaming, and a Society of AI agents.

```bash
python cli.py generate "SaaS billing app with auth and payments" --production --build
```

---

## What VibeCober Does

VibeCober is an **agentic software factory** — a full-stack platform where AI agents collaborate to design, build, test, and document software from a natural language description.

| You Say | You Get |
| ------- | ------- |
| `"todo app"` | SQLAlchemy models, FastAPI routes, pytest suite |
| `"SaaS with auth and payments"` | JWT auth, DB schema, Docker, deployment config |
| `"API for a blog with comments"` | Full CRUD endpoints, user management, tests |

One command. Production-ready output.

---

## Architecture Overview

```text
User Idea
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                  VibeCober Platform                  │
│                                                     │
│  CLI ──────────────────────► PipelineRunner         │
│                                    │                │
│  Web UI (NovaIDE) ─► REST/WS API  │                │
│                          │         ▼                │
│                     FastAPI    TeamLeadBrain         │
│                     Backend         │               │
│                          │    Orchestrator          │
│                          │         │               │
│                          ▼         ▼               │
│               Society Agents   Classic Pipeline     │
│               (8 specialists)  (7 agents)           │
└─────────────────────────────────────────────────────┘
```

---

## Agent Ecosystem

### Classic Pipeline (Deterministic)

| Agent | Responsibility | Output |
| ----- | -------------- | ------ |
| **Team Lead Brain** | Decides which agents run | JSON execution plan |
| **Planner** | Architecture & tech stack | Module breakdown |
| **DB Schema** | Database design | SQLAlchemy models |
| **Auth** | Authentication system | JWT routes + security |
| **Coder** | Project skeleton & code | Files and folders |
| **Tester** | Test suite generation | pytest suite |
| **Deployer** | Deployment configuration | Dockerfile, compose, Makefile |
| **Code Reviewer** | Quality assurance | Annotated review |

### Society of Agents (Multi-Agent Coordination)

An advanced orchestration mode where specialized agents communicate via a **MessageBus**, produce structured documents, and coordinate with human-in-the-loop approval.

| Agent | Role |
| ----- | ---- |
| **Society Product Manager** | Captures requirements, writes PRD |
| **Society Architect** | System design and technology choices |
| **Society API Designer** | OpenAPI specification |
| **Society Engineer** | Code implementation |
| **Society QA** | Test plans and quality gates |
| **Society DevOps** | Infrastructure and deployment |
| **Society Tech Writer** | Documentation and user guides |
| **Society Project Manager** | Coordination and task tracking |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- An LLM API key (Anthropic Claude or NVIDIA NIM)

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/vibecober.git
cd vibecober
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY or NIM_API_KEY
```

### 2. Install Backend

```bash
pip install -r backend/requirements.txt
```

### 3. Install Frontend

```bash
cd frontend && npm install
```

### 4. Run the Platform

```bash
# Terminal 1 — Backend API
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend (NovaIDE)
cd frontend && npm run dev
```

Open `http://localhost:5173` in your browser.

Windows helper scripts: `start-backend.bat`, `start-frontend.bat`, `start.bat`

---

## CLI Usage

```bash
python cli.py generate "<your idea>" [flags]
```

### Generation Modes

| Flag | Description | Agents |
| ---- | ----------- | ------ |
| `--simple` | Prototype mode | Planner + Coder |
| `--full` | Standard (default) | Planner + DB + Auth + Coder |
| `--production` | Full stack | All 7 agents |

### Additional Flags

| Flag | Description |
| ---- | ----------- |
| `--build` | Write files to disk |
| `--output ./path` | Custom output directory |
| `--skip-tests` | Skip test generation |
| `--no-docker` | Skip Docker files |
| `--tier free/pro/enterprise` | Token budget tier |

### Examples

```bash
# Quick prototype
python cli.py generate "weather app" --simple

# Blog with auth (no Docker)
python cli.py generate "blog with users" --full --no-docker --build

# Production SaaS with all agents
python cli.py generate "SaaS invoicing app with auth" --production --build --output ./my-saas

# View execution logs
python cli.py logs <project_id>
```

---

## Web Interface — NovaIDE

The frontend at `http://localhost:5173` provides a full-featured IDE experience:

| Route | Description |
| ----- | ----------- |
| `/` | Landing page |
| `/ide` | **NovaIDE** — resizable panels (file tree, editor, agent chat, terminal) |
| `/dashboard` | Project history and management |
| `/new-project` | Society Agents wizard — step-by-step project creation with document review |
| `/run` | Run view — generated documents and artifacts |

### NovaIDE Features

- **Monaco Editor** — VS Code-quality code editing with syntax highlighting
- **Integrated Terminal** — xterm.js terminal via WebSocket
- **Agent Chat** — Real-time chat with the orchestrator
- **File Explorer** — Browse and edit generated project files
- **Resizable Panels** — Drag-to-resize layout

### New Project Wizard (`/new-project`)

Uses the Society of Agents with:

- Real-time **WebSocket progress streaming** per agent
- Per-agent progress bars and status indicators
- Document viewer with **markdown rendering**
- Human-in-the-loop document approval
- Document feedback and revision requests

---

## Project Structure

```text
vibecober/
├── cli.py                          # CLI entry point
├── backend/
│   ├── main.py                     # FastAPI app + 25 route registrations
│   ├── database.py                 # SQLAlchemy engine (SQLite/PostgreSQL)
│   ├── api/                        # HTTP + WebSocket route handlers (24 files)
│   │   ├── auth.py                 # JWT login/register
│   │   ├── society.py              # Society agents + /ws/updates/{run_id}
│   │   ├── atoms_engine.py         # Multi-agent race mode
│   │   ├── studio.py               # IDE file/terminal API
│   │   ├── snapshot.py             # Time-travel snapshots
│   │   ├── agent_chat.py           # Anthropic API proxy
│   │   └── ...                     # +16 more routers
│   ├── agents/                     # 28 specialized AI agents
│   │   ├── team_lead_brain.py      # Master orchestrator
│   │   ├── planner.py / coder.py / db_schema.py / auth_agent.py
│   │   ├── tester.py / deploy_agent.py / code_reviewer.py
│   │   ├── society_*.py            # 8 society specialist agents
│   │   └── auto_fixer.py           # LLM-powered bug fixer
│   ├── core/
│   │   ├── orchestrator.py         # v1/v2 pipeline facade
│   │   ├── pipeline_runner.py      # Deterministic pipeline execution
│   │   ├── llm_client.py           # NIM / Anthropic gateway
│   │   ├── documents/              # 9 structured document types (PRD, API spec, etc.)
│   │   ├── orchestration/
│   │   │   ├── society_orchestrator.py       # Society workflow coordinator
│   │   │   └── multi_project_orchestrator.py # Concurrent multi-project execution
│   │   ├── communication/
│   │   │   └── message_bus.py      # Inter-agent async message queue
│   │   ├── observability/
│   │   │   ├── tracer.py           # Distributed tracing
│   │   │   ├── metrics.py          # Metric collection
│   │   │   └── prometheus_metrics.py # Prometheus exposition
│   │   ├── learning/
│   │   │   ├── failure_analyzer.py  # Pattern-matched failure diagnosis + PatternMatcher
│   │   │   ├── reflector.py        # Agent self-reflection
│   │   │   └── improvement_engine.py # Learning from past runs
│   │   ├── reflection/
│   │   │   └── reflection_system.py # LLM-powered self-critique
│   │   ├── optimization/
│   │   │   └── model_selector.py   # Smart LLM model selection by task
│   │   ├── memory/                 # Agent working memory
│   │   └── human_loop/             # HITL approval workflows
│   ├── engine/
│   │   ├── circuit_breaker.py      # Fault tolerance (open/half-open/closed)
│   │   ├── token_ledger.py         # Per-agent token accounting
│   │   ├── token_governance.py     # Budget enforcement (free/pro/enterprise)
│   │   ├── sandbox.py              # Isolated execution environment
│   │   ├── snapshot_manager.py     # Time-travel run snapshots
│   │   ├── race_mode.py            # Parallel agent racing
│   │   ├── auto_fixer.py           # LLM test-fix loop engine
│   │   ├── state_machine_expanded.py # Run state machine
│   │   └── ...                     # +10 more engine modules
│   ├── models/                     # 14 SQLAlchemy ORM models
│   ├── schemas/                    # Pydantic request/response schemas
│   ├── services/                   # Business logic (deployment, testing, diff)
│   ├── tools/                      # Shell executor, MCP integration
│   ├── utils/                      # JSON parser, command validator, logger
│   ├── auth/                       # JWT + BCrypt security
│   ├── alembic/                    # Database migrations
│   └── tests/                      # 84-test pytest suite (all passing)
│       ├── test_circuit_breaker.py
│       ├── test_budget_enforcement.py
│       ├── test_sandbox.py
│       ├── test_snapshot_manager.py
│       ├── test_document_system.py
│       ├── test_society_system.py
│       ├── test_state_machine_expanded.py
│       └── test_e2e_smoke.py
├── frontend/
│   └── src/
│       ├── router.tsx              # React Router 6 route definitions
│       ├── main.tsx                # App entry point
│       ├── components/
│       │   ├── NovaIDE.tsx         # Main IDE (resizable panels)
│       │   ├── AgentChat.tsx       # Agent chat interface
│       │   ├── AtomsChatPanel.tsx  # Atoms engine chat
│       │   └── society/
│       │       ├── AgentDashboard.tsx   # Real-time agent progress (WebSocket)
│       │       └── DocumentViewer.tsx   # Markdown-rendered document viewer
│       ├── pages/
│       │   ├── Dashboard.tsx       # Project history
│       │   ├── NewProject.tsx      # Society agents wizard
│       │   └── RunView.tsx         # Run documents view
│       ├── lib/
│       │   ├── society-api.ts      # Society API client + WebSocket subscriptions
│       │   ├── api.ts              # Base HTTP client
│       │   └── atmos-state.ts      # ATMOS pipeline state
│       ├── stores/
│       │   ├── ide-store.ts        # IDE state (Zustand)
│       │   └── agent-store.ts      # Agent state (Zustand)
│       └── core/
│           └── orchestrator.ts     # Frontend agent orchestrator
└── run_logs/                       # Execution + token governance logs
```

---

## API Reference

The backend exposes **24 API routers** at `http://localhost:8000`:

### Key Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/api/auth/register` | Create user account |
| `POST` | `/api/auth/login` | Login, receive JWT |
| `POST` | `/api/generate` | Generate project from idea |
| `POST` | `/api/society/runs` | Start Society agents workflow |
| `GET` | `/api/society/runs/{run_id}` | Poll run status |
| `GET` | `/api/society/runs/{run_id}/documents` | List generated documents |
| `GET` | `/api/society/runs/{run_id}/metrics` | Token + timing metrics |
| `GET` | `/api/society/runs/{run_id}/traces` | Execution trace logs |
| `WS` | `/api/society/ws/updates/{run_id}` | **WebSocket** real-time events |
| `POST` | `/api/society/documents/{doc_id}/approve` | Approve a document (HITL) |
| `POST` | `/api/society/documents/{doc_id}/feedback` | Request revision |
| `POST` | `/api/atoms/run` | Run atoms multi-agent pipeline |
| `GET` | `/api/snapshot/list/{run_id}` | List time-travel snapshots |
| `POST` | `/api/snapshot/restore` | Restore a snapshot |
| `GET` | `/api/circuit-breakers` | Circuit breaker statuses |
| `GET` | `/health` | Health check |
| `GET` | `/api/status` | API version and status |

### WebSocket Events (`/ws/updates/{run_id}`)

```json
{ "type": "agent_started",   "agent": "society_architect",  "data": {} }
{ "type": "agent_completed", "agent": "society_architect",  "data": { "doc_id": "doc_abc123" } }
{ "type": "agent_failed",    "agent": "society_engineer",   "data": { "error": "..." } }
{ "type": "status",          "data": { "status": "running", "doc_ids": [] } }
{ "type": "completed",       "data": { "run_id": "...", "doc_ids": [] } }
{ "type": "ping" }
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=sqlite:///./vibecober.db
# DATABASE_URL=postgresql://user:pass@host/db

# Auth
JWT_SECRET_KEY=your-secret-key-here

# LLM Provider (choose one or both)
ANTHROPIC_API_KEY=sk-ant-...
NIM_API_KEY=nvapi-...
NIM_MODEL=deepseek-ai/deepseek-r1-0528

# Token Budget Tiers
FREE_DAILY_CAP_USD=1.00
PRO_DAILY_CAP_USD=10.00

# Environment
ENV=development
CORS_ORIGINS=http://localhost:5173

# Storage
ARTIFACT_BACKEND=local
```

---

## Advanced Features

### Token Governance

Every agent run is tracked and budget-enforced:

- **Free tier** — $1.00/day default cap
- **Pro tier** — $10.00/day
- **Enterprise tier** — Configurable
- Per-agent token ledger with cost reporting
- Budget exceeded raises `BudgetExceededError` with full usage summary

### Circuit Breakers

Wraps all LLM and external API calls:

- **Closed** — Normal operation
- **Open** — Fails fast after N consecutive failures
- **Half-open** — Test with single call before recovering
- Registry accessible at `GET /api/circuit-breakers`

### Failure Analyzer

Pattern-matched failure diagnosis with 10 built-in patterns:

| Pattern | Symptoms | Confidence |
| ------- | -------- | ---------- |
| Indentation Error | `indentationerror`, `unexpected indent` | 0.93 |
| Python Syntax Error | `syntaxerror`, `invalid syntax` | 0.92 |
| Execution Timeout | `timeout`, `deadline exceeded` | 0.95 |
| JSON Parse Error | `jsondecodeerror`, `invalid json` | 0.90 |
| Import Error | `no module named`, `importerror` | 0.90 |
| Auth Error | `401`, `unauthorized` | 0.85 |
| Attribute Error | `attributeerror`, `has no attribute` | 0.87 |
| Type Error | `typeerror`, `unsupported operand` | 0.85 |
| Runtime Error | `runtimeerror`, `zerodivisionerror` | 0.88 |
| Key Error | `keyerror`, `key not found` | 0.88 |

High-confidence matches (≥ 0.90) bypass LLM — instant diagnosis.

### Auto-Fixer Engine

LLM-powered test-fix loop with:

- **Fast path** — pattern match at ≥ 0.9 confidence, no LLM call
- **LLM loop** — up to `max_attempts` (default 3) iterations
- Optional async `validator` callable to verify each fix
- Full `FixAttempt` history with per-attempt confidence scores

### Time-Travel Snapshots

Capture and restore any point in a run:

```bash
POST /api/snapshot/create          # Capture current state
GET  /api/snapshot/list/{run_id}   # List checkpoints
POST /api/snapshot/restore         # Restore to snapshot
```

### Multi-Project Orchestrator

Run up to N projects concurrently with semaphore-based throttling:

```python
orchestrator = MultiProjectOrchestrator(max_concurrent=5)
await orchestrator.start()
run_id = await orchestrator.submit_project("My SaaS idea")
```

### Race Mode

Submit the same task to multiple agents in parallel — fastest correct answer wins.

---

## Running Tests

```bash
# Run all 84 backend tests
cd backend && pytest

# Run specific suite
pytest tests/test_society_system.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

Current status: **84/84 passing**

| Test File | Tests | Focus |
| --------- | ----- | ----- |
| `test_budget_enforcement.py` | 13 | Token ledger + budget caps |
| `test_circuit_breaker.py` | 12 | Circuit breaker state machine |
| `test_document_system.py` | 9 | Document store + message bus |
| `test_e2e_smoke.py` | 2 | End-to-end pipeline smoke |
| `test_sandbox.py` | 10 | Isolated execution environment |
| `test_snapshot_manager.py` | 7 | Time-travel snapshots |
| `test_society_system.py` | 26 | Society agents full integration |
| `test_state_machine_expanded.py` | 4 | Run state machine transitions |
| **Total** | **84** | **All passing** |

---

## Database Management

```bash
# Run all migrations
cd backend && alembic upgrade head

# Create a new migration after model changes
cd backend && alembic revision --autogenerate -m "add column"

# Rollback one migration
cd backend && alembic downgrade -1
```

---

## Deployment

### Docker (Generated Projects)

```bash
cd output/

# Development
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up -d --build

# Run tests inside container
docker-compose run --rm api pytest
```

### Railway (VibeCober Platform)

The project includes `railway.json` for one-click Railway deployment.
Set all `.env` variables in the Railway dashboard.

---

## Generation Output Structure

```text
output/
├── backend/
│   └── app/
│       ├── main.py           # FastAPI application
│       ├── database.py       # SQLAlchemy setup
│       ├── models/           # ORM models
│       ├── routes/           # API endpoints
│       └── auth/
│           ├── security.py   # Hashing + JWT
│           ├── dependencies.py
│           └── routes.py     # /register /login /me
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_health.py
├── Dockerfile
├── Dockerfile.dev
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── requirements.txt
├── .env.production
└── DEPLOY.md
```

---

## Technology Stack

### Backend

| Layer | Technology |
| ----- | ---------- |
| API Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.x |
| Validation | Pydantic v2 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | JWT (python-jose) + BCrypt |
| Migrations | Alembic |
| Rate Limiting | SlowAPI |
| LLM Providers | Anthropic Claude, NVIDIA NIM |
| Testing | Pytest + pytest-asyncio |

### Frontend

| Layer | Technology |
| ----- | ---------- |
| Framework | React 18 + TypeScript |
| Build Tool | Vite |
| Routing | React Router 6 |
| Styling | TailwindCSS + Radix UI |
| State | Zustand |
| Editor | Monaco Editor |
| Terminal | xterm.js |
| Animations | Framer Motion, GSAP |

---

## Changelog

### v1.0.0 — Society Agents & Real-Time IDE

- **Society of 8 agents** with structured document output and HITL approval
- **WebSocket streaming** — real-time per-agent progress events
- **NovaIDE** — resizable panels (editor, file tree, agent chat, terminal)
- **Multi-project orchestrator** — N concurrent projects with semaphore control
- **Failure Analyzer** — 10 pattern-matched failure categories + `PatternMatcher`
- **Auto-Fixer** — LLM test-fix loop with fast-path pattern bypass
- **Token governance** — per-tier budget caps with enforcement
- **Circuit breakers** — fault-tolerant LLM + API calls
- **Time-travel snapshots** — capture and restore any run checkpoint
- **Prometheus metrics** — `/metrics` endpoint for monitoring
- **Distributed tracing** — per-run agent execution traces
- **84 tests** — full coverage across all systems
- Python 3.14 compatibility — all deprecated APIs updated

### v0.3.0 — Agentic Architecture

- Team Lead Brain orchestrator
- 7-agent deterministic pipeline
- CLI with mode flags (`--simple`, `--full`, `--production`)
- Docker deployment generation
- Test suite generation

---

## License

MIT License — Use freely, build boldly.

---

Built with discipline. Designed for developers.
