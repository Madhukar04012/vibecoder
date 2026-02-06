# Changelog

All notable changes to VibeCober.

## [0.3.1] - 2026-02-06

### Fixed

- **CORS**: Removed invalid `*` with `credentials=True`; use explicit localhost origins
- **Auth API**: Added `/auth/register` alias for `/auth/signup` (common convention)
- **JWT**: Ensure `sub` claim is always string for UUID compatibility
- **Build**: Merge auth, tester, deployer outputs into project build (was only using coder)
- **LLM Client**: Cross-platform Ollama path (Linux/Mac use `ollama` from PATH)
- **test_flow.py**: Self-contained test (signup before login)
- **FolderTree**: Fixed duplicate React keys in project preview

### Added

- **Frontend**: Real API integration - calls `/generate/project` instead of mock data
- **Frontend**: Error display when generation fails
- **Frontend**: CLI command hint on build completion
- **.env.example**: `OLLAMA_PATH` for custom Ollama location

---

## [0.3.0] - 2026-02-04

### 🧠 Phase 2: Agentic Architecture

**Complete multi-agent pipeline with Team Lead Brain.**

### Added

- **Team Lead Brain** (`team_lead_brain.py`)
  - Analyzes project ideas and decides agent execution plan
  - Supports 3 modes: simple, full, production
  - Deterministic JSON output

- **DB Schema Agent** (`db_schema.py`)
  - Generates SQLAlchemy models from architecture
  - Handles relationships and foreign keys
  - Outputs ready-to-use Python code

- **Auth Agent** (`auth_agent.py`)
  - Generates JWT authentication system
  - Creates security utilities (bcrypt, JWT)
  - Generates protected routes

- **Test Agent** (`test_agent.py`)
  - Generates pytest test suite
  - Includes conftest fixtures
  - Auth and health test coverage

- **Deploy Agent** (`deploy_agent.py`)
  - Generates Dockerfile (dev + prod)
  - Generates docker-compose files
  - Creates Makefile and DEPLOY.md

- **Agent Registry** (`agent_registry.py`)
  - Central catalog of all agents
  - Dynamic agent loading
  - Dependency tracking

### Changed

- **Orchestrator v2** - Now uses Team Lead Brain for decisions
- **CLI** - Added mode flags: `--simple`, `--full`, `--production`
- **CLI** - Added skip flags: `--skip-tests`, `--no-docker`
- **CLI** - Added legacy mode: `--v1`

### Architecture

```
User Idea → Team Lead Brain → Agent Execution Plan → Orchestrator → Output
```

7-agent pipeline:
1. Team Lead Brain (decision)
2. Planner (architecture)
3. DB Schema (models)
4. Auth (security)
5. Coder (structure)
6. Tester (validation)
7. Deployer (production)

---

## [0.2.0] - Previous

- Initial agent pipeline (planner + coder)
- Basic CLI
- Project structure generation

---

## [0.1.0] - Initial

- Project scaffolding
- FastAPI backend setup
