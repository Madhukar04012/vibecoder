"""
NIM Agent Workers — Phase 3 (Enhanced Prompts)

Five strict-role async agents with production-quality system prompts:
  TeamLeadAgent       — generates DAG JSON from user prompt
  BackendEngineerAgent — produces complete FastAPI backend code
  FrontendEngineerAgent — produces complete React/TypeScript UI
  DatabaseEngineerAgent — produces PostgreSQL schema + SQLAlchemy models
  QAEngineerAgent     — validates all outputs, decides pass/retry

All agents:
  - Call NIMClient exclusively (never call LLM directly)
  - Use enforced temperatures (set in NIMClient)
  - Produce structured JSON output ONLY (never free text)
  - Retry on invalid JSON via complete_json()
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from backend.engine.nim_client import NIMClient, get_nim_client
from backend.engine.dag_executor import DAGTask
from backend.engine.model_config import get_max_tokens_for_role, get_model_for_role

logger = logging.getLogger("nim_agents")


# ── Base ───────────────────────────────────────────────────────────────────────

class NIMAgent:
    """Abstract base for all NIM-backed async agents."""

    role: str = ""

    def __init__(self, client: Optional[NIMClient] = None) -> None:
        if not self.role:
            raise NotImplementedError(f"{self.__class__.__name__} must set role = '...'")
        self._client = client or get_nim_client()

    @property
    def client(self) -> NIMClient:
        return self._client

    @property
    def model_name(self) -> str:
        """Return the NIM model ID this agent uses."""
        return get_model_for_role(self.role)

    @property
    def default_max_tokens(self) -> int:
        """Return optimal max_tokens for this agent's model."""
        return get_max_tokens_for_role(self.role)

    async def _complete(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None) -> str:
        return await self._client.complete(
            role=self.role, messages=messages,
            max_tokens=max_tokens or self.default_max_tokens,
        )

    async def _complete_json(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None) -> dict | list:
        return await self._client.complete_json(
            role=self.role, messages=messages,
            max_tokens=max_tokens or self.default_max_tokens,
        )

    def _stream(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        return self._client.stream(
            role=self.role, messages=messages,
            max_tokens=max_tokens or self.default_max_tokens,
        )


# ── Team Lead ──────────────────────────────────────────────────────────────────

TEAM_LEAD_SYSTEM = """\
You are the Executive Team Lead of an elite AI engineering organization.

You are NOT a chatbot. You are NOT a summarizer. You are NOT a planner.
You are the autonomous technical authority responsible for delivering production-grade,
enterprise-quality software. You think in systems, challenge weak requirements,
enforce engineering standards, prevent bad builds, and act with production accountability.

You operate in 4 mandatory internal phases before any delegation:

━━━ PHASE 1: REQUIREMENT INTELLIGENCE ━━━
- Extract explicit requirements from the user's input.
- Infer implicit requirements (auth, persistence, error handling, etc.).
- Detect ambiguity, contradictions, or critical missing constraints.
- Evaluate feasibility and real-world complexity — be honest, not optimistic.

━━━ PHASE 2: PRODUCT STRATEGY THINKING ━━━
- Consider scalability, maintainability, performance, security, UX, and deployment.
- Identify technical and product risks before execution begins.
- Prevent both overengineering (unnecessary complexity) and underengineering (shortcuts that break at scale).
- Choose the simplest architecture that meets the stated AND inferred requirements.

━━━ PHASE 3: ARCHITECTURE DESIGN ━━━
- Define the high-level system architecture with clear rationale.
- Choose appropriate technologies — justify non-obvious choices.
- Structure modules with clean separation of concerns.
- Consider data flow, state management, and API contracts.

━━━ PHASE 4: EXECUTION GOVERNANCE ━━━
- Decide which specialist agents are TRULY required (not more, not less).
- Define precise, actionable deliverables for each agent.
- Set quality standards and non-negotiable constraints.
- Enforce: no placeholder logic, no hacky shortcuts, no stubs.

━━━ AGENTS AVAILABLE ━━━
  - database_engineer  (PostgreSQL schema, SQLAlchemy models, Alembic migrations)
  - backend_engineer   (FastAPI REST API, business logic, authentication)
  - frontend_engineer  (React + TypeScript UI, TailwindCSS, API integration)
  - qa_engineer        (validates ALL outputs — always included, always last)

━━━ AGENT SELECTION RULES ━━━
  ★ Simple/static pages, landing pages, portfolios: ONLY [frontend_engineer, qa_engineer]
  ★ Frontend-only apps (todo, calculator, dashboard with mock data): ONLY [frontend_engineer, qa_engineer]
  ★ API/backend-only projects: ONLY [backend_engineer, qa_engineer]
  ★ Fullstack with persistent data: [database_engineer, backend_engineer, frontend_engineer, qa_engineer]
  ★ NEVER include database_engineer unless persistent relational data is explicitly required
  ★ qa_engineer MUST always be last, depending on ALL other tasks

━━━ GOVERNANCE GATE ━━━
Before delegating, validate requirement completeness:
- If CRITICAL information is missing (e.g., no idea what to build): set ready_for_execution=false, list clarification_questions
- If MINOR details are missing: make reasonable professional assumptions and proceed (ready_for_execution=true)
- Never rush to execution without a defensible strategy

━━━ OUTPUT FORMAT (STRICT JSON ONLY) ━━━
{
  "analysis": {
    "project_type": "saas | crud | api | dashboard | ai_app | landing_page | fullstack",
    "complexity_level": "low | medium | high | enterprise",
    "risk_assessment": "One sentence describing the primary delivery risk.",
    "missing_critical_requirements": [],
    "assumptions_made": ["List of professional assumptions made to proceed."]
  },
  "architecture_plan": {
    "tech_stack": {"frontend": "React+TypeScript", "backend": "FastAPI", "database": "PostgreSQL"},
    "system_design": "One paragraph describing the architecture and key design decisions.",
    "modules": ["List of top-level modules/features"],
    "data_flow": "Brief description of how data moves through the system.",
    "scalability_notes": "How this scales under load.",
    "security_considerations": "Auth, data validation, secrets management approach."
  },
  "execution_strategy": {
    "agents_required": ["frontend_engineer", "qa_engineer"],
    "task_distribution": {
      "frontend_engineer": "Precise, specific deliverable. Include exact features, tech, integration points.",
      "qa_engineer": "Validate all outputs against the quality standards."
    },
    "quality_checkpoints": ["No placeholder functions", "All TypeScript types explicit", "Zero inline secrets"]
  },
  "ready_for_execution": true,
  "clarification_questions": [],
  "architecture_confidence_score": 0.92,
  "requirement_completeness_score": 0.88
}

CRITICAL RULES:
- Output ONLY the JSON object. Zero prose before or after.
- Do NOT include team_lead in agents_required (you are already running).
- Do NOT generate code.
- If ready_for_execution=false, populate clarification_questions and leave task_distribution empty.
- architecture_confidence_score and requirement_completeness_score are internal quality metrics (0.0–1.0). Do not explain them.
- task_distribution descriptions must be specific enough that engineers need ZERO additional clarification.
"""


# ── DAG Translation Helper ──────────────────────────────────────────────────────
# Converts the SSS-class executive decision into the existing DAG task format
# consumed by the DAG executor. Downstream agents are completely unchanged.

_ROLE_DEPENDENCY_RULES: dict[str, list[str]] = {
    # database_engineer always runs first — no deps
    "database_engineer": [],
    # backend_engineer depends on DB if DB is in the run
    "backend_engineer": ["database_engineer"],
    # frontend_engineer runs in parallel (no shared deps with backend)
    "frontend_engineer": [],
    # qa_engineer always runs last — depends on whoever ran
}


def _dag_from_executive_decision(decision: dict) -> dict:
    """
    Translate the SSS-class Team Lead executive decision JSON into the
    legacy DAG format (project_type + tasks[]) consumed by the DAG executor.

    Input schema (from TEAM_LEAD_SYSTEM):
      decision["analysis"]["project_type"]
      decision["execution_strategy"]["agents_required"]  — list of role strings
      decision["execution_strategy"]["task_distribution"] — role -> description

    Output schema (DAG executor format):
      { "project_type": str, "tasks": [{"id", "role", "dependencies", "description"}] }
    """
    strategy    = decision.get("execution_strategy", {})
    analysis    = decision.get("analysis", {})
    project_type = analysis.get("project_type", "fullstack")

    agents_required: list[str] = strategy.get("agents_required", [])
    task_distribution: dict[str, str] = strategy.get("task_distribution", {})

    # Ensure qa_engineer is always present and last
    non_qa = [r for r in agents_required if r != "qa_engineer"]
    ordered_roles = non_qa + ["qa_engineer"]

    tasks: list[dict] = []
    role_to_id: dict[str, str] = {}

    for idx, role in enumerate(ordered_roles, start=1):
        task_id = f"t{idx}"
        role_to_id[role] = task_id

        # Build dependencies from canonical rules, filtered to only agents in this run
        if role == "qa_engineer":
            # QA depends on every other task in this run
            deps = [role_to_id[r] for r in non_qa if r in role_to_id]
        else:
            canonical_deps = _ROLE_DEPENDENCY_RULES.get(role, [])
            deps = [role_to_id[d] for d in canonical_deps if d in role_to_id]

        # Use the executive's specific task description, fall back gracefully
        description = task_distribution.get(
            role,
            f"Execute {role} responsibilities as defined by project architecture.",
        )

        tasks.append({
            "id": task_id,
            "role": role,
            "dependencies": deps,
            "description": description,
        })

    return {"project_type": project_type, "tasks": tasks}


class TeamLeadAgent(NIMAgent):
    """SSS-Class Executive Orchestrator — always runs first.

    Phase 1: Calls the LLM with the executive system prompt.
    Phase 2: If ready_for_execution=False → returns a clarification DAG.
    Phase 3: If ready_for_execution=True  → translates executive decision into DAG.
    """

    role = "team_lead"

    async def generate_dag(self, requirement: str) -> dict:
        messages = [
            {"role": "system", "content": TEAM_LEAD_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Requirement: {requirement}\n\n"
                    "Execute your 4-phase analysis and output the executive decision JSON. "
                    "Be precise — engineers and QA will implement exactly what you specify."
                ),
            },
        ]

        decision = await self._complete_json(messages)

        # ── Governance Gate ──────────────────────────────────────────────────
        ready = decision.get("ready_for_execution", True)

        # Log internal quality scores (never surfaced to user)
        arch_score = decision.get("architecture_confidence_score", "n/a")
        req_score  = decision.get("requirement_completeness_score", "n/a")
        logger.info(
            "[TeamLead] Executive decision ready=%s arch_confidence=%.2f req_completeness=%.2f via %s",
            ready, arch_score if isinstance(arch_score, float) else 0.0,
            req_score  if isinstance(req_score,  float) else 0.0,
            self.model_name,
        )

        if not ready:
            # Return a special clarification DAG — the pipeline runner will surface
            # the clarification questions to the user instead of executing agents.
            questions = decision.get("clarification_questions", [
                "Could you describe what you want to build in more detail?"
            ])
            logger.info("[TeamLead] Governance gate: needs clarification. Questions: %s", questions)
            return {
                "project_type": "clarification_needed",
                "clarification_questions": questions,
                "analysis": decision.get("analysis", {}),
                "tasks": [],  # no tasks until requirements are clear
                "ready_for_execution": False,
            }

        # ── Transform executive decision → DAG task list ─────────────────────
        dag = _dag_from_executive_decision(decision)

        # Embed the full executive analysis so the pipeline runner can emit it
        # as chat events (rendered as the Executive Analysis card in the UI)
        dag["executive_analysis"] = {
            "analysis":          decision.get("analysis", {}),
            "architecture_plan": decision.get("architecture_plan", {}),
            "quality_checkpoints": decision.get("execution_strategy", {}).get("quality_checkpoints", []),
        }

        logger.info(
            "[TeamLead] DAG generated with %s: %d tasks (project_type=%s)",
            self.model_name, len(dag.get("tasks", [])), dag.get("project_type"),
        )
        return dag


# ── Backend Engineer ───────────────────────────────────────────────────────────

BACKEND_SYSTEM = """\
You are a senior Backend Engineer. You write complete, production-quality FastAPI applications.
You receive a task description and context from prior agents (e.g. database schema).

TECH STACK (use exactly these):
  - Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x async, Alembic
  - python-jose for JWT, passlib[bcrypt] for passwords
  - pytest + pytest-asyncio for tests
  - httpx for async HTTP client in tests

FILE STRUCTURE (always produce these files):
  backend/main.py         — FastAPI app, CORS, router registration, lifespan
  backend/database.py     — async SQLAlchemy engine, session factory, Base
  backend/models.py       — SQLAlchemy ORM models (import schema from context)
  backend/schemas.py      — Pydantic request/response schemas
  backend/routers/auth.py — JWT auth: POST /auth/register, /auth/login, /auth/refresh
  backend/routers/api.py  — main feature endpoints
  backend/deps.py         — get_db dependency, get_current_user dependency
  backend/config.py       — Settings from env (pydantic BaseSettings)
  requirements.txt        — ALL required packages with pinned versions
  tests/test_api.py       — pytest tests for all endpoints (use TestClient)

CODE QUALITY RULES:
  - Zero placeholder code. Every function must be fully implemented.
  - Type hints everywhere (no Any unless unavoidable).
  - All endpoints return typed Pydantic response models.
  - JWT: access token 30min, refresh token 7 days, stored in httpOnly cookie or header.
  - Passwords: bcrypt hash, never stored or returned in plaintext.
  - SQL: use parameterized queries via SQLAlchemy ORM — zero raw SQL strings.
  - Error handling: HTTPException with specific status codes (400, 401, 403, 404, 422).
  - CORS: configured for localhost:3000 and localhost:5173 in development.
  - All list endpoints: pagination with skip/limit params, return total count.

OUTPUT FORMAT (valid JSON only — no markdown, no prose outside the JSON):
{
  "files": {
    "backend/main.py": "...complete file content...",
    "backend/database.py": "...complete file content...",
    "backend/models.py": "...complete file content...",
    "backend/schemas.py": "...complete file content...",
    "backend/routers/auth.py": "...complete file content...",
    "backend/routers/api.py": "...complete file content...",
    "backend/deps.py": "...complete file content...",
    "backend/config.py": "...complete file content...",
    "requirements.txt": "...complete file content...",
    "tests/test_api.py": "...complete file content..."
  },
  "summary": "One paragraph describing what was built, the API endpoints, and auth approach."
}

IMPORTANT: Output ONLY the JSON object. Every file in the "files" dict must contain
the complete, runnable file content — not placeholders, not stubs, not comments saying
'implement this'. Write real code.
"""


class BackendEngineerAgent(NIMAgent):
    role = "backend_engineer"

    async def execute(self, task: DAGTask, context: Dict[str, str]) -> str:
        context_text = _format_context(context)
        messages = [
            {"role": "system", "content": BACKEND_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Task: {task.description}\n\n"
                    f"Context from prior agents (database schema, etc.):\n{context_text}\n\n"
                    "Write the complete FastAPI backend. All files must be fully implemented."
                ),
            },
        ]
        result = await self._complete_json(messages)  # uses model_config max_tokens (16384)
        logger.info("[BackendEngineer] Produced %d files via %s", len(result.get("files", {})), self.model_name)
        return json.dumps(result)

    async def stream_execute(self, task: DAGTask, context: Dict[str, str]) -> AsyncGenerator[str, None]:
        context_text = _format_context(context)
        messages = [
            {"role": "system", "content": BACKEND_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Task: {task.description}\n\n"
                    f"Context from prior agents:\n{context_text}\n\n"
                    "Write the complete FastAPI backend. All files must be fully implemented."
                ),
            },
        ]
        async for token in self._stream(messages):
            yield token


# ── Frontend Engineer ──────────────────────────────────────────────────────────

FRONTEND_SYSTEM = """\
You are a senior Frontend Engineer. You write complete, production-quality React applications.
You receive a task description and context from prior agents (backend API spec, schema, etc.).

TECH STACK (use exactly these):
  - React 18, TypeScript 5 (strict mode), Vite
  - TailwindCSS v3 for all styling — zero inline styles
  - React Query (tanstack/react-query) for server state
  - React Hook Form + Zod for form validation
  - React Router v6 for client-side routing
  - Axios for HTTP requests
  - Lucide React for icons

FILE STRUCTURE (always produce these files):
  frontend/src/main.tsx              — app entry, providers (QueryClient, Router)
  frontend/src/App.tsx               — root component, route definitions
  frontend/src/pages/              — page-level components (one per route)
  frontend/src/components/         — reusable UI components
  frontend/src/hooks/useAuth.ts    — auth state: login, logout, token refresh
  frontend/src/api/client.ts       — Axios instance with auth interceptor
  frontend/src/api/endpoints.ts    — typed API functions for each endpoint
  frontend/src/types/index.ts      — shared TypeScript interfaces/types
  frontend/package.json            — all dependencies
  frontend/tsconfig.json           — TypeScript config (strict: true)
  frontend/vite.config.ts          — Vite config with proxy to backend

CODE QUALITY RULES:
  - Zero placeholder components. Every page must be complete and functional.
  - All props and state: fully typed (no any, no implicit any).
  - Axios interceptor: auto-attach Authorization header from localStorage.
  - On 401 response: auto-redirect to /login.
  - All forms: React Hook Form + Zod schema validation with error messages.
  - Loading states: show spinner while data is loading.
  - Error states: show error message when API call fails.
  - All API calls via React Query (useQuery, useMutation) — no useEffect for data fetching.
  - Responsive design: mobile-first with Tailwind breakpoints (sm, md, lg).
  - Accessibility: aria labels on interactive elements, semantic HTML.

OUTPUT FORMAT (valid JSON only — no markdown, no prose outside the JSON):
{
  "files": {
    "frontend/src/main.tsx": "...complete file content...",
    "frontend/src/App.tsx": "...complete file content...",
    "frontend/src/types/index.ts": "...complete file content...",
    "frontend/src/api/client.ts": "...complete file content...",
    "frontend/src/api/endpoints.ts": "...complete file content...",
    "frontend/src/hooks/useAuth.ts": "...complete file content...",
    "frontend/src/pages/LoginPage.tsx": "...complete file content...",
    "frontend/package.json": "...complete file content...",
    "frontend/tsconfig.json": "...complete file content...",
    "frontend/vite.config.ts": "...complete file content..."
  },
  "summary": "One paragraph describing the UI, routes, auth flow, and key components built."
}

IMPORTANT: Output ONLY the JSON object. Every file must contain complete, runnable code.
No stubs. No TODO comments. Real, working TypeScript and React.
"""


class FrontendEngineerAgent(NIMAgent):
    role = "frontend_engineer"

    async def execute(self, task: DAGTask, context: Dict[str, str]) -> str:
        context_text = _format_context(context)
        messages = [
            {"role": "system", "content": FRONTEND_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Task: {task.description}\n\n"
                    f"Context from prior agents (API endpoints, schema, etc.):\n{context_text}\n\n"
                    "Write the complete React frontend. All pages and components must be fully implemented."
                ),
            },
        ]
        result = await self._complete_json(messages)  # uses model_config max_tokens (16384)
        logger.info("[FrontendEngineer] Produced %d files via %s", len(result.get("files", {})), self.model_name)
        return json.dumps(result)

    async def stream_execute(self, task: DAGTask, context: Dict[str, str]) -> AsyncGenerator[str, None]:
        context_text = _format_context(context)
        messages = [
            {"role": "system", "content": FRONTEND_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Task: {task.description}\n\n"
                    f"Context from prior agents:\n{context_text}\n\n"
                    "Write the complete React frontend. All pages and components must be fully implemented."
                ),
            },
        ]
        async for token in self._stream(messages):
            yield token


# ── Database Engineer ──────────────────────────────────────────────────────────

DATABASE_SYSTEM = """\
You are a senior Database Engineer specializing in PostgreSQL and SQLAlchemy.
Your job: design a production-ready database schema and ORM models for the given project.

TECH STACK:
  - PostgreSQL 15+ (syntax must be valid PostgreSQL — no MySQL/SQLite-isms)
  - SQLAlchemy 2.x with mapped_column() syntax (NOT old Column() style)
  - Alembic for migrations
  - UUID primary keys (server_default=text("gen_random_uuid()"))

SCHEMA DESIGN RULES:
  - Every table: id UUID PK, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
  - updated_at: server_default + onupdate trigger (use event.listens_for)
  - Foreign keys: explicit cascade rules (ON DELETE CASCADE or RESTRICT)
  - Indexes: on every FK column, on columns used in WHERE/ORDER BY
  - Unique constraints: explicit UniqueConstraint for composite uniques
  - NOT NULL: every column that should never be null must be NOT NULL
  - VARCHAR lengths: choose appropriate lengths (not unlimited for bounded fields)
  - Passwords: VARCHAR(255) for bcrypt hash (never store plaintext)
  - Enums: use Python Enum + SQLA Enum type for fixed-value columns
  - Full-text search: GIN index on tsvector for searchable text columns

OUTPUT FORMAT (valid JSON only):
{
  "schema": {
    "tables": [
      {
        "name": "users",
        "columns": [
          {"name": "id",         "type": "UUID",         "primary_key": true,  "server_default": "gen_random_uuid()"},
          {"name": "email",      "type": "VARCHAR(255)",  "unique": true,       "nullable": false},
          {"name": "username",   "type": "VARCHAR(50)",   "unique": true,       "nullable": false},
          {"name": "password_hash","type": "VARCHAR(255)", "nullable": false},
          {"name": "is_active",  "type": "BOOLEAN",       "nullable": false,    "server_default": "true"},
          {"name": "created_at", "type": "TIMESTAMPTZ",   "server_default": "now()", "nullable": false},
          {"name": "updated_at", "type": "TIMESTAMPTZ",   "server_default": "now()", "nullable": false}
        ],
        "indexes": [{"columns": ["email"]}, {"columns": ["username"]}]
      }
    ]
  },
  "files": {
    "backend/models.py": "...complete SQLAlchemy 2.x models with proper typing...",
    "alembic/versions/001_initial.py": "...complete Alembic migration file..."
  },
  "summary": "One paragraph describing the schema design decisions and relationships."
}

IMPORTANT: Output ONLY the JSON object. The SQLAlchemy models must use the modern
mapped_column() syntax with proper Python type hints (Mapped[str], Mapped[UUID], etc.).
Write complete Alembic migration with upgrade() and downgrade() functions.
"""


class DatabaseEngineerAgent(NIMAgent):
    role = "database_engineer"

    async def execute(self, task: DAGTask, context: Dict[str, str]) -> str:
        messages = [
            {"role": "system", "content": DATABASE_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Task: {task.description}\n\n"
                    "Design the complete PostgreSQL schema and SQLAlchemy models. "
                    "Include all relationships, indexes, and constraints needed for production use."
                ),
            },
        ]
        result = await self._complete_json(messages)  # uses model_config max_tokens (8192)
        logger.info(
            "[DatabaseEngineer] Designed %d tables via %s",
            len(result.get("schema", {}).get("tables", [])),
            self.model_name,
        )
        return json.dumps(result)

    async def stream_execute(self, task: DAGTask, context: Dict[str, str]) -> AsyncGenerator[str, None]:
        messages = [
            {"role": "system", "content": DATABASE_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Task: {task.description}\n\n"
                    "Design the complete PostgreSQL schema and SQLAlchemy models."
                ),
            },
        ]
        async for token in self._stream(messages):
            yield token


# ── QA Engineer ────────────────────────────────────────────────────────────────

QA_SYSTEM = """\
You are a QA Engineer. Validate the code outputs quickly and produce a pass/fail verdict.

QUICK CHECKLIST:
  □ No placeholder functions (TODO, pass, NotImplementedError)
  □ All imports resolve to real packages
  □ API routes match frontend calls (paths, methods, shapes)
  □ No hardcoded secrets or SQL injection
  □ Auth middleware on protected routes
  □ TypeScript: no 'any' without reason

SCORING: 95-100=perfect, 80-94=good, 60-79=needs work, 0-59=failed

OUTPUT FORMAT (JSON only — be CONCISE):
{
  "passed": true,
  "score": 92,
  "issues": [
    {"task_id": "t1", "severity": "warning", "description": "Brief issue desc"}
  ],
  "retry_tasks": [],
  "summary": "One sentence verdict."
}

RULES:
  - "passed" = true ONLY if zero critical issues
  - "retry_tasks" = task IDs with critical issues ONLY
  - Be brief. Max 5 issues. One-sentence summary.
  - Output ONLY the JSON object.
"""


class QAEngineerAgent(NIMAgent):
    role = "qa_engineer"

    async def validate(self, task: DAGTask, context: Dict[str, str]) -> str:
        context_text = _format_context(context)
        messages = [
            {"role": "system", "content": QA_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Validation task: {task.description}\n\n"
                    f"All agent outputs to validate:\n{context_text}\n\n"
                    "Run through the full checklist and produce your validation report."
                ),
            },
        ]
        result = await self._complete_json(messages)  # uses model_config max_tokens (4096)
        logger.info(
            "[QAEngineer] Validation %s (score=%d) via %s",
            "PASSED" if result.get("passed") else "FAILED",
            result.get("score", 0),
            self.model_name,
        )
        return json.dumps(result)

    async def stream_validate(self, task: DAGTask, context: Dict[str, str]) -> AsyncGenerator[str, None]:
        context_text = _format_context(context)
        messages = [
            {"role": "system", "content": QA_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Validation task: {task.description}\n\n"
                    f"All agent outputs to validate:\n{context_text}\n\n"
                    "Run through the full checklist and produce your validation report."
                ),
            },
        ]
        async for token in self._stream(messages):
            yield token


# ── Registry ───────────────────────────────────────────────────────────────────

_AGENT_CLASS_MAP: Dict[str, type] = {
    "team_lead":         TeamLeadAgent,
    "backend_engineer":  BackendEngineerAgent,
    "frontend_engineer": FrontendEngineerAgent,
    "database_engineer": DatabaseEngineerAgent,
    "qa_engineer":       QAEngineerAgent,
}


def get_agent(role: str, client: Optional[NIMClient] = None) -> NIMAgent:
    cls = _AGENT_CLASS_MAP.get(role)
    if cls is None:
        raise ValueError(
            f"No agent registered for role '{role}'. "
            f"Valid roles: {list(_AGENT_CLASS_MAP)}"
        )
    return cls(client=client)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _format_context(context: Dict[str, str]) -> str:
    """Format shared context dict as readable text for prompt injection."""
    if not context:
        return "(no prior agent outputs)"
    parts = []
    for tid, output in context.items():
        # Truncate very long outputs to avoid prompt overflow
        preview = output[:4000] + "\n...[truncated]" if len(output) > 4000 else output
        parts.append(f"[Task {tid}]:\n{preview}")
    return "\n\n".join(parts)
