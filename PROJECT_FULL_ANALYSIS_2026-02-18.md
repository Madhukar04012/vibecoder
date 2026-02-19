# VibeCober Full Project Analysis

Date: 2026-02-18  
Repository: `vibecober`  
Revision analyzed: `af3a156` (working tree is dirty with many in-progress changes)

## 1) Executive Summary

VibeCober is an ambitious multi-surface AI software factory with three active generations of architecture running in one repository:

1. Unified pipeline (recommended core): `PipelineRunner` with strict contracts, retries, state machine, budget governance, artifact versioning, and memory indexing.
2. Atoms streaming runtime: `/api/atoms/stream` now routes standard mode through the unified pipeline, but keeps large legacy code paths (especially race mode and deployment glue).
3. Society document workflow: a separate document-first orchestrator with multi-project scaling and self-improvement subsystems.

The project has strong core orchestration foundations and good observability primitives. The main risks are security exposure from unauthenticated command-execution endpoints, architecture sprawl across overlapping runtimes, and quality drift in frontend tests and UI governance.

## 2) Scope and Method

This analysis was based on direct review of:

- Core backend orchestration, engine, API, auth, storage, memory, and tooling modules.
- Frontend routing, IDE shell, event bus, orchestration bridge, and society pages.
- Test suites and practical test execution on this machine.
- Operational artifacts in `run_logs/`.

Key verification commands run:

- `pytest backend/tests -q -k "not society"` -> 55 passed, 29 deselected.
- `pytest backend/tests/test_society_system.py -q` -> timed out at 180s.
- `pytest backend/tests/test_society_system.py::TestReflectionAgent::test_reflect_on_success -q` -> 1 passed (slow: ~28s).
- `npm --prefix frontend run typecheck` -> passed.
- `npm --prefix frontend test` -> failed (3/3 tests in `NovaIDE.test.tsx`).

## 3) Current Project Topology

High-level size snapshot:

- Backend files: 199
- Frontend source files: 71
- Backend test files: 10
- API route decorators detected: 117
- Routers included in app: 24

Primary entry points:

- CLI: `cli.py`
- Backend app: `backend/main.py`
- Unified pipeline: `backend/core/pipeline_runner.py`
- Web stream engine: `backend/api/atoms_engine.py`
- Frontend app bootstrap: `frontend/src/main.tsx`
- Frontend router: `frontend/src/router.tsx`
- Primary IDE shell: `frontend/src/components/NovaIDE.tsx`

## 4) Architecture Overview

### 4.1 Unified Generation Core (Best Structured Path)

`PipelineRunner` (`backend/core/pipeline_runner.py`) is the strongest architectural center:

- Builds deterministic execution plan from Team Lead Brain.
- Enforces agent output contracts (`backend/core/contracts.py`).
- Applies retries with capped exponential backoff.
- Enforces state transitions via `EngineStateMachine`.
- Tracks spend via `TokenLedger` and per-tier daily caps via `TokenGovernance`.
- Persists generated artifacts with versions and zip bundles.
- Indexes artifact content into scoped memory store.
- Emits JSONL run logs and agent metrics.

Observed strengths:

- Explicit lifecycle and state history in returned payload.
- Good run metadata: budget pre/post, cost breakdown, artifacts, memory scope.
- Non-critical agent degradation path (`tester`, `deployer`) supports partial success.

### 4.2 API Surface

`backend/main.py` mounts 24 routers with broad capabilities:

- Auth/projects/tasks/runs/messages/artifacts.
- Generate and execution surfaces.
- Atoms stream and ATMOS.
- Studio and terminal endpoints.
- Society workflow and governance endpoints.

This is powerful but currently overloaded: several overlapping pathways perform similar generation/execution responsibilities.

### 4.3 Frontend Runtime

The web frontend is React + Zustand + event-bus driven:

- Router protects `/ide`, `/dashboard`, `/new-project`, `/run`.
- `NovaIDE` composes chat + file panel + editor + preview.
- `AtomsChatPanel` drives `runAtmosIntent` and hydrates IDE state from SSE events.
- `ide-bridge` exposes `window.ideAPI` for tool-based agent actions.
- Society pages are integrated (`NewProject`, `RunView`) using `/api/society/*`.

## 5) Execution Flows

### 5.1 CLI Flow

`cli.py generate` -> `PipelineRequest` -> `run_pipeline` -> optional `build_project`.

Modes:

- `--simple`: planner + coder
- `--full`: default
- `--production`: all configured agents

Build merges coder + auth + tester + deployer outputs before writing files.

### 5.2 Atoms Web Flow

Frontend `runAtmosIntent` posts to `/api/atoms/stream`.

Server behavior:

- Standard mode currently uses `_stream_unified_standard`, which wraps `PipelineRunner`.
- Emits mapped SSE events for agent lifecycle, execution plan, budget, files, preview.
- Auto-deploy behavior writes generated files, runs `npm install`, and starts Vite preview.

Race mode remains legacy and separate.

### 5.3 Society Flow

`/api/society/workflow` spins a per-run `SocietyOrchestrator`:

- PRD -> system design -> API spec -> task breakdown
- Parallel engineer execution
- QA, DevOps, Tech Writer
- Document store + websocket event streaming

This is architecturally separate from the unified generation core.

## 6) Data, Storage, and Observability

Persistence layers in use:

- SQLAlchemy relational models (`users`, `projects`, `tasks`, `runs`, `artifacts`, etc.).
- Alembic migration baseline: `2026_02_06_33585cadc9c0_initial_schema.py`.
- Local JSONL run logs in `run_logs/`.
- Agent aggregate metrics in `run_logs/agent_stats.json`.
- Token governance ledger in `run_logs/token_governance.json`.
- Versioned file artifacts in `generated_projects/artifacts/`.
- In-memory scoped semantic index (FAISS if installed, deterministic fallback otherwise).

Operational evidence from current logs:

- `planner` has the highest average duration in current stats.
- `code_reviewer` is also expensive in duration.
- Last observed planner contract failure: `frontend` returned `None` instead of `str`.

## 7) Quality and Testing Posture

### 7.1 Backend

Status:

- Core backend tests (excluding society suite): healthy.
- 55 tests passed across budget, circuit breaker, document store, e2e smoke, sandbox, snapshots, state machine.

Gap:

- `test_society_system.py` is slow/unstable in this environment and exceeded 180s timeout.
- At least one targeted society test passes, but suite-level reliability needs work.

### 7.2 Frontend

Type safety:

- `tsc --noEmit` passes.

Test reliability:

- `NovaIDE.test.tsx` fails completely.
- Failures are due to missing required providers (`Router`, `ThemeProvider`) and stale assumptions/snapshot.

Conclusion:

- Frontend test coverage is very thin and currently non-green.

## 8) Security Assessment (Highest Priority Findings)

### Critical

1. Unauthenticated command execution endpoint:
- `backend/api/run.py` exposes `POST /api/run` with `shell=True`.
- No auth dependency.
- Direct remote command execution risk.

2. Unauthenticated terminal endpoints:
- `backend/api/terminal_ws.py` (`/api/terminal/create`, `/api/terminal/execute`, websocket terminal).
- No auth dependency.
- Enables remote interactive command execution.

### High

3. Studio command execution is still `shell=True`:
- `backend/api/studio.py` validates commands, but endpoint is unauthenticated and still shell-based.
- Better than raw execution, but remains a high-value attack surface.

4. Hardcoded local telemetry sink in frontend:
- `frontend/src/components/AtomsChatPanel.tsx` posts to `http://127.0.0.1:7242/ingest/...`.
- Should be feature-flagged or removed from production paths.

5. Agent chat proxy not auth-gated:
- `backend/api/agent_chat.py` accesses paid Anthropic API via server key.
- Without auth, this can be abused for cost burn.

## 9) Architectural Risks and Drift

1. Runtime overlap:
- Unified pipeline, Atoms legacy internals, ATMOS, chat stream generator, and MetaGPT endpoint coexist.
- Similar responsibilities appear in multiple modules with different safety/quality profiles.

2. Monolithic Atoms API module:
- `backend/api/atoms_engine.py` mixes old and new pipelines, build/deploy orchestration, file streaming, and preview process management.
- Hard to reason about and test in isolation.

3. Governance/process drift:
- Internal UI freeze rules in `AGENTS.md` are not reflected by current `NovaIDE`/`AtomsChatPanel` content.
- Indicates mismatch between intended and actual frontend shell constraints.

4. Cost accounting inconsistency risk:
- Pricing table marks some default NIM models as zero-cost.
- Real vendor billing and internal governance may diverge without explicit reconciliation.

## 10) What Is Working Well

1. Unified runner has clear contracts and lifecycle governance.
2. Artifact versioning + bundle generation is practical and production-friendly.
3. Memory scoping model is clean and extensible.
4. Observability output (JSONL + aggregate stats) is useful for debugging and governance.
5. Backend non-society test set is healthy and catches core regressions.
6. Frontend type-check baseline is passing.

## 11) Recommended Action Plan

### Immediate (0-7 days)

1. Protect or disable unsafe execution endpoints:
- Require auth for `/api/run`, `/api/terminal/*`, `/studio/execute`.
- Prefer disabling `/api/run` entirely in production.

2. Remove hardcoded ingest calls from frontend or guard behind dev-only flags.

3. Add CI gate for:
- `pytest backend/tests -k "not society"`
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend test` (after test fix)

### Short Term (1-3 weeks)

1. Refactor `backend/api/atoms_engine.py`:
- Extract deployment/process-management services.
- Keep one standard execution path for non-race mode.

2. Fix frontend tests:
- Add render helper with Router + Theme providers.
- Update obsolete assertions/snapshots.

3. Stabilize society tests:
- Mock expensive orchestration paths.
- Split fast unit tests from long integration tests.

### Medium Term (1-2 months)

1. Consolidate generation runtimes:
- Decide canonical path between unified pipeline vs legacy streams.
- Deprecate redundant endpoints cleanly.

2. Move governance persistence from local JSON to database-backed store for multi-process safety.

3. Add endpoint-level security policy documentation and automated security tests for auth enforcement.

## 12) Final Assessment

VibeCober has a solid core in the unified pipeline and enough platform surface to become a strong AI engineering runtime. The key blocker to production-grade readiness is not feature completeness; it is security hardening and architectural consolidation. Addressing the critical execution endpoint exposure and reducing runtime overlap will materially increase reliability and maintainability.

