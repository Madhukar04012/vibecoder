# VibeCober — Full Project Analysis (Line-by-Line)

This document is a **line-by-line and section-by-section** analysis of the VibeCober codebase: entry points, backend, frontend, and how they connect.

---

## Table of Contents

1. [Project overview](#1-project-overview)
2. [Root & CLI](#2-root--cli)
3. [Backend — main.py](#3-backend--mainpy)
4. [Backend — core (orchestrator, pipeline, contracts)](#4-backend--core)
5. [Backend — engine (state, atoms, tokens)](#5-backend--engine)
6. [Backend — agents (team lead brain, planner, coder)](#6-backend--agents)
7. [Backend — API routers](#7-backend--api-routers)
8. [Frontend — entry & router](#8-frontend--entry--router)
9. [Frontend — IDE shell (NovaIDE)](#9-frontend--ide-shell-novaide)
10. [Frontend — IDE store](#10-frontend--ide-store)
11. [Frontend — multi-agent chat (Agents panel)](#11-frontend--multi-agent-chat)
12. [Data flow summary](#12-data-flow-summary)

---

## 1. Project overview

**What VibeCober is**

- **AI-powered project generator**: user describes an idea → backend runs a pipeline of agents (planner, db_schema, auth, coder, tester, deployer, etc.) → outputs architecture + file structure + optional files on disk.
- **Two execution paths**:
  - **CLI** (`cli.py`): `generate "idea"` uses `PipelineRunner` (Team Lead Brain + agents); `run backend/frontend/all` calls HTTP APIs to run engineer agents on a project.
  - **Web (Atoms)**: frontend IDE at `/ide`; “Atoms” chat runs the same pipeline via Atoms Engine API; “Agents” chat is a separate frontend-only multi-agent system (Mike/Alex/Iris) that uses Claude + IDE tools.
- **Backend**: FastAPI, SQLAlchemy, Pydantic; agents use LLM (NIM/DeepSeek by default); unified pipeline with contracts, token governance, observability.
- **Frontend**: React + TypeScript, Vite, Zustand, Monaco; single IDE shell (NovaIDE) with file tree, editor, terminal, and two chat modes (Atoms vs Agents).

**High-level layout**

```
User → CLI or Web
  → Backend: PipelineRunner / Atoms Engine
    → Team Lead Brain (execution plan)
    → Agents (planner → db_schema → auth → coder → …)
    → Artifacts, memory, token ledger
  → Frontend: NovaIDE
    → Atoms chat → backend pipeline (SSE/API)
    → Agents chat → frontend AgentOrchestrator (Claude) + window.ideAPI (IDE tools)
```

---

## 2. Root & CLI

### `cli.py` — Line-by-line

| Lines | Purpose |
|-------|--------|
| 1–20 | Shebang, encoding fix, imports (`sys`, `argparse`, `requests`). `API_BASE = "http://127.0.0.1:8000"`, `AUTH_TOKEN` for run/logs. |
| 23–29 | `main()`: argparse root parser, `subparsers` for `generate`, `run`, `logs`. |
| 31–48 | **generate** subparser: `idea`, `--build`, `--output`, `--simple`/`--full`/`--production`, `--skip-tests`, `--no-docker`, `--v1`, `--tier`, `--project-id`, `--memory-scope`. |
| 50–74 | **run** subparser: `run backend/frontend/all` with `project_id`, `--all`, `--token`. **logs** subparser: `project_id`, `--token`. |
| 76–91 | Parse args; route to `handle_generate`, `handle_run_backend`, `handle_run_frontend`, `handle_run_all`, `handle_logs`, or `print_help`. |
| 95–237 | **handle_generate**: If `use_v2` (default): build `PipelineRequest`, call `run_pipeline()`, print execution plan, agent outputs (planner, db_schema, auth, tester, deployer, coder), run state, cost, budget. If `--build`: `merge_agent_outputs` + `build_project(structure, output_dir)` and print created files. Else v1: `run_agents(idea)` (planner + coder only), print architecture and structure. |
| 240–295 | **handle_run_backend**: Resolve token; POST `/agents/backend/{id}/run` or `.../run-all`; print result and recent logs. |
| 298–341 | **handle_run_frontend**: Same pattern for frontend agent. |
| 344–419 | **handle_run_all**: Run backend run-all then frontend run-all; aggregate completed/failed; print summary and logs. |
| 422–378 | **handle_logs**: GET summary and logs for project; print execution history. |
| 411–421 | **Helpers**: `_get_token()` from `VIBECOBER_TOKEN`; `print_structure()` recursive dict printer. |
| 424–425 | `if __name__ == "__main__": main()`. |

**Summary**: CLI is the main CLI entry point: generate (v2 pipeline or v1 legacy), run backend/frontend/all (HTTP), logs. No direct DB access; all goes through backend API.

---

## 3. Backend — main.py

### Line-by-line

| Lines | Purpose |
|-------|--------|
| 1–25 | Docstring (v0.6.1 + Phase-2). Imports: FastAPI, CORS, static files, logging. Logging configured to INFO, stderr. |
| 27–47 | DB: `Base`, `engine` from `backend.database`. Import all API routers (auth, projects, team_lead, tasks, agents, logs, generate, runs, messages, artifacts, studio, metagpt_engine, chat_stream, chat_simple, run, atoms_engine, terminal_ws, hitl, marketplace, snapshot, atmos, pipeline_governance). Import models so they’re registered. |
| 52–74 | **`_validate_env()`**: In production, require `DATABASE_URL`, `JWT_SECRET_KEY` and reject default secret; in dev, warn if default. |
| 77–78 | `Base.metadata.create_all(bind=engine)` — create tables on startup. |
| 79–84 | **Lifespan**: on startup call `_validate_env()`; yield; no shutdown logic. |
| 86–93 | **FastAPI app**: title, description, version 0.7.0, lifespan. |
| 95–104 | **CORS**: `CORS_ORIGINS` env (comma list or `*`); allow credentials only when origins are not `*`. |
| 106–154 | **Include routers** in order: auth, projects, team_lead, tasks, agents, logs, generate; runs, messages, artifacts; studio; metagpt_engine; chat_stream; chat_router at `/api`; run_router; atoms_router; terminal_router; hitl_router; marketplace_router; snapshot_router; atmos_router; pipeline_governance_router. |
| 158–165 | **Global exception handler**: log exception, return 500 JSON. |
| 168–184 | **Misc routes**: `/api/status`, `/api/circuit-breakers`, `/api/race-mode/history`, `/api/prompt-optimizer/stats`, `/health`. |
| 199–219 | **SPA serve**: If `frontend/dist` exists, mount `/assets`, and catch-all `/{full_path:path}` to serve `index.html` or static files. |

**Summary**: Single FastAPI app: DB init, env validation, CORS, all routers mounted, global error handling, health/status, optional frontend SPA serve.

---

## 4. Backend — core

### `core/orchestrator.py`

- **Purpose**: Facade for “run agents.” No direct execution; delegates to pipeline or legacy v1.
- **`run_agents_v2(idea, mode)`**: Builds `PipelineRequest` (idea, mode, channel=cli, user_id=local-cli, memory_scope=project), calls `run_pipeline(request)`.
- **`run_agents(idea)`**: Legacy: `planner_agent(idea)` → `code_agent(architecture, idea)`; returns input_idea, architecture, project_structure.
- **`orchestrate(idea, mode, use_v2)`**: If `use_v2` then `run_agents_v2`, else `run_agents`.

### `core/pipeline_runner.py` (summary)

- **PipelineRequest**: idea, mode, run_id, channel, user_id, project_id, token_tier, memory_scope, memory_version, retries, timeout, clear_memory_before_run.
- **PipelineRunner**: Holds request, context (on_event, strict_contracts), run_id, state_machine, plan, agent_outputs, metrics, logger, memory_scope_key, artifact_store, governance.
- **`run()`**: Emit run_started; start ledger; configure budget; optionally clear memory; transition PLANNING → create_execution_plan → WAITING_FOR_APPROVAL → EXECUTING; for each agent in execution_order run `_run_agent_with_retries`; persist artifacts; index memory; transition to COMPLETED/PARTIAL_SUCCESS; return result (success, state, cost, agent_outputs, etc.).
- **Agent execution**: Get agent function from registry; validate output against contract; retry with backoff on contract failure; record metrics and ledger.

### `core/contracts.py`

- Defines expected shapes per agent (e.g. planner, db_schema, coder). `validate_agent_output(agent_name, output)` raises `AgentContractError` if invalid.

### `core/agent_registry.py`

- Maps agent name (string) to callable. `get_agent_function(name)` returns the function that runs that agent (used by PipelineRunner).

---

## 5. Backend — engine

### `engine/state.py`

- **EngineState** enum: IDLE, PLANNING, WAITING_FOR_APPROVAL, EXECUTING, REVIEWING, QA, PARTIAL_SUCCESS, AWAITING_HUMAN, FAILED, CANCELLED, TIMEOUT, COMPLETED (plus aliases APPROVED, EXECUTION).
- **ALLOWED_AGENTS**: Which agent names are allowed in which state (e.g. EXECUTING allows planner, db_schema, auth, coder, …).
- **VALID_TRANSITIONS**: Allowed state transitions. **EngineStateMachine**: Holds current state; `transition(new_state)` checks VALID_TRANSITIONS and updates state.

### `engine/atoms_engine.py`

- **AtomsEngine**: Web-facing wrapper. Holds run_id, project_id, user_id, token_tier, state_machine, events, prd, roadmap, files, validation, qa_result, diagram state.
- **`run(user_prompt)`**: Builds `PipelineRequest` (idea=user_prompt, mode=full, channel=web, …), calls `run_unified_pipeline(request, PipelineContext(on_event=_forward_event))`. Bridges runner events into Atoms event emitter. After run: sync state from result state_history; set prd, roadmap, qa_result, validation, files from result; check for Mermaid diagram; return Atoms-shaped payload (success, error, blocked, state, prd, roadmap, files, validation, qa_result, cost, run_id, pipeline_result).
- **`get_cost_summary()`**, **`reset()`**, **`acknowledge_diagram()`** for cost, reset, and diagram ack.

### `engine/token_ledger.py`

- Tracks token usage and cost per run/agent. **ledger**: start_run, record_agent, get_summary, reset. Used by pipeline and governance.

### `engine/token_governance.py`

- **TokenTier** (free, pro, enterprise) with daily caps. **get_token_governance()**: checks budget before/after run; can block execution if over cap.

---

## 6. Backend — agents

### `agents/team_lead_brain.py`

- **ExecutionPlan**: project_type, complexity, agents list, execution_order, config (skip_tests, strict_mode, depth).
- **TeamLeadBrain**: AVAILABLE_AGENTS set, AGENT_DEPENDENCIES dict. **`decide(idea)`**: Analyze idea (keyword/LLM); determine project_type, complexity, needs (auth, db, tests, deploy); build ordered agent list from dependencies and mode (simple/full/production); return ExecutionPlan.
- **`create_execution_plan(idea, mode)`**: Module-level function that instantiates TeamLeadBrain(mode) and returns `decide(idea)`.

### Other agents (conceptual)

- **planner**: Takes idea; returns architecture (backend, frontend, database, modules).
- **db_schema**: Takes planner output; returns schema (tables, columns).
- **auth**: JWT/auth strategy and routes.
- **coder**: Takes planner (and optionally schema/auth); returns project_structure (nested dict of files/folders).
- **tester**, **deployer**, **code_reviewer**: Tests, Docker/deploy, review. All invoked by PipelineRunner via agent_registry; outputs validated by contracts.

---

## 7. Backend — API routers

- **auth**: Login/signup, JWT issue, get_current_user dependency.
- **projects**: CRUD projects; list for user.
- **team_lead**: Execution plan (idea → plan).
- **tasks**: Task CRUD per project.
- **agents**: Run backend/frontend agent (single or run-all) for a project; return task results.
- **logs**: Execution logs per project; summary endpoint.
- **generate**: Generate project (may call pipeline).
- **runs, messages, artifacts**: MetaGPT-style run/message/artifact records.
- **studio**: Workspace/IDE API (e.g. run commands, execute).
- **metagpt_engine**: Alternative engine entry.
- **chat_stream**: Streaming chat (Replit-style).
- **chat_simple**: Simple chat for connectivity.
- **run**: Code execution (e.g. run command).
- **atoms_engine**: Web pipeline: start run, SSE events, get state/cost; uses AtomsEngine.run().
- **terminal_ws**: WebSocket terminal; create session, execute command, get status.
- **hitl**: Human-in-the-loop clarification cards.
- **marketplace**: Atom manifest/registry.
- **snapshot**: Time-travel snapshots.
- **atmos**: ATMOS autonomous pipeline (AI-only).
- **pipeline_governance**: Token/budget and governance endpoints.

---

## 8. Frontend — entry & router

### `main.tsx`

- **1–7**: React, ReactDOM, RouterProvider, router from `./router`, ErrorBoundary, SettingsProvider, `./index.css`.
- **9–17**: `createRoot(document.getElementById("root")).render()`: StrictMode → ErrorBoundary → SettingsProvider → RouterProvider(router). No AuthProvider here; it’s inside router.

### `router.tsx`

- **createBrowserRouter** with one parent route and children.
- **Parent element**: ThemeProvider → AuthProvider → Outlet, Analytics, SpeedInsights.
- **RequireAuth**: If not authenticated, Navigate to `/login`.
- **RedirectIfAuth**: If authenticated, Navigate to `/ide` (used on login/signup).
- **Routes**:
  - `/` → VibeCober (landing).
  - `/login` → RedirectIfAuth(Login).
  - `/signup` → RedirectIfAuth(Signup).
  - `/ide` → RequireAuth(NovaIDE).
  - `/dashboard` → RequireAuth(Dashboard).

**Summary**: App shell is Theme + Auth + router. IDE and dashboard are protected; login/signup redirect to IDE when already logged in.

---

## 9. Frontend — IDE shell (NovaIDE)

### `components/NovaIDE.tsx`

- **ViewMode**: `'editor' | 'viewer'` (Code vs Preview).
- **ChatMode**: `'atoms' | 'agents'` (Atoms chat vs multi-agent Agents chat).
- **State**: viewMode, chatMode, previewUrl, phase from atmos store.
- **Effects**: Restore IDE state on boot; on ATMOS_PHASE_CHANGE set viewMode to viewer when live, editor when generating; **install IDE bridge** once: `installIdeAPI(useIDEStore.getState)`, cleanup `uninstallIdeAPI`.
- **Layout**: Horizontal Group (react-resizable-panels):
  - **Left panel (atmos-chat)**: Chat mode tabs (Atoms | Agents); then either AtomsChatPanel or AgentChat.
  - **Separator** (drag).
  - **Right panel (atmos-editor)**: Top bar (Code / Preview tabs, preview URL badge). Below: either editor view (FilePanel + EditorPanel) or preview view (iframe or “No preview”).
- **CSS**: Uses `var(--ide-*)` for colors and borders (atoms-ide-layout.css). No extra marketing copy (frozen UI rules).

**Summary**: NovaIDE is the single IDE shell: chat (Atoms or Agents), file tree, editor, terminal (inside EditorPanel), preview. IDE bridge is installed here so Agents chat tools can call into the store.

---

## 10. Frontend — IDE store

### `stores/ide-store.ts`

**Types**

- **WorkspaceMode**: 'empty' | 'project'.
- **ProjectState**: 'no_project' | 'loaded' | 'ai_running'.
- **ProjectInfo**: id, name, path?.
- **TerminalLine**: type (command/stdout/stderr), text.
- **ChatMessage**: id, role, content, optional agentName, agentIcon, toAgent, messageType, eventType, eventData, files, isStreaming.
- **FileStatus**: isNew, isModified, isAIGenerated, isLiveWriting.
- **AIStatus**, **AgentStep**: for Atoms pipeline UI.

**State (Zustand)**

- **Tabs**: openFiles[], activeFile, fileContents{}, fileStatuses{}. **openFile(path)**: add/move path in openFiles, ensure path in fileContents, set activeFile, update recentlyOpenedFiles and activeContextFiles. **closeFile**: remove path, fix activeFile. **setActiveFile**, **updateFileContent**.
- **Workspace**: workspaceMode, setWorkspaceMode, resetToEmptyWorkspace.
- **Project**: projectState, project, setProject, setProjectState.
- **Activity**: activityLog, addActivity, clearActivity (passive).
- **Awareness**: recentlyOpenedFiles, recentlyModifiedFiles, activeContextFiles, markOpened, markModified, setActiveContext.
- **Terminal**: terminalLines[], appendTerminalLine (trim to last 500), clearTerminal.
- **Chat**: chatMessages[], addChatMessage, updateLastAssistantMessage, appendToLastAssistantMessage, clearChat.
- **AI status**: aiStatus, setAIStatus, aiCurrentFile, setAICurrentFile, aiFileProgress, setAIFileProgress, fileLiveWriting, setFileLiveWriting.
- **File ops from chat**: createFile(path, content, openAfter?), appendToFile(path, delta). createFile updates fileContents, fileStatuses, openFiles, activeFile.
- **Agent steps**: agentSteps[], addAgentStep, completeAgentStep, clearAgentSteps.

**Persistence**

- Subscribe to store; persist only openFiles and activeFile to localStorage (atmos:ide:v1). **restoreIDEState()**: Restore openFiles/activeFile only if fileContents has content for those paths (avoid ghost tabs).

**Summary**: Single source of truth for IDE: tabs, file contents, terminal lines, chat messages (Atoms), AI status, file creation/append, agent steps. Used by FilePanel, EditorPanel, TerminalPanel, AtomsChatPanel, and by the IDE bridge for the Agents tools.

---

## 11. Frontend — multi-agent chat (Agents panel)

This is the “Agents” tab in the left panel: Mike (team lead), Alex (engineer), Iris (researcher), Emma, Sarah; Claude API; tools call into the IDE via `window.ideAPI`.

### `agents/definitions.ts`

- **AgentDefinition**: name, role, system_prompt, can_use_tools, can_delegate_to[].
- **AGENTS**: mike (team leader; delegates to alex, iris, emma, sarah; no tools), alex (engineer; tools; no delegation), iris (researcher), emma (designer), sarah (QA). Each has a system_prompt describing behavior and “Current project workspace: /workspace”.

### `tools/index.ts`

- **Tool**: name, description, execute(params) → Promise<unknown>.
- **Window.ideAPI** (global): readFile, writeFile, listFiles, runCommand, openFile, refreshFileTree.
- **IDE_TOOLS**: read_file (path → content, path), write_file (path, content → success, path; calls refreshFileTree), list_files (path? → files[]), run_terminal (command → output, error), open_file_in_editor (path → success). All call `window.ideAPI`; tools are used by the orchestrator when Alex runs.

### `core/orchestrator.ts`

- **Message**: role, agent, content, timestamp. **ProjectState**: messages[], tasks[], current_agent, token_usage.
- **AgentOrchestrator**:
  - **Constructor**: Init Anthropic client if `VITE_ANTHROPIC_API_KEY` is set; init state (messages, tasks, current_agent=mike, token_usage); store onMessage callback.
  - **handleUserMessage(userInput)**: Append user message to state; route with routeMessage(input); runAgent(startAgent, userInput).
  - **routeMessage**: If input contains @alex/@iris/@emma/@sarah return that agent; else mike.
  - **buildMessagesForAPI**: Convert state.messages to Anthropic format (assistant messages prefixed with [AGENT]:).
  - **buildToolDefinitions**: Map IDE_TOOLS to Anthropic tool schema (name, description, input_schema with path, content, command).
  - **runAgent(agentName, input)**: Get agent def; if no client show “set API key” message. Call client.messages.create with system=agent.system_prompt, messages, tools if agent.can_use_tools. Then processResponse.
  - **processResponse**: For each content block: if text, accumulate and parseDelegation (DELEGATE_TO:name or @name); if delegation, addAgentMessage and runAgent(delegated, brief); if tool_use, executeTool and continueAgentWithToolResult (send tool_result back to Claude, get next message, process again); else addAgentMessage.
  - **parseDelegation**: Regex for DELEGATE_TO:(\w+)\n… or @(\w+)…; return { agent, brief }.
  - **executeTool**: Find tool by name in IDE_TOOLS, run execute(params).
  - **continueAgentWithToolResult**: New messages.create with previous assistant content + user content = tool_result; then processResponse again.
  - **addAgentMessage**: Push to state.messages and call onMessage (updates UI).

### `lib/ide-bridge.ts`

- **installIdeAPI(getState)**: getState = `() => useIDEStore.getState()`. Sets **window.ideAPI**:
  - **readFile(path)**: normalize path (strip /workspace and leading /); find key in fileContents (exact or suffix match); return content or "".
  - **writeFile(path, content)**: normalize path; if path in fileContents then updateFileContent else createFile(path, content, true).
  - **listFiles(path?)**: If no path return all fileContents keys; else filter keys by prefix (path or path/).
  - **runCommand(command)**: appendTerminalLine(`$ ${command}`, "command") and a note line; return { stdout: "Command echoed to terminal.", stderr: "" } (no backend execution in this bridge).
  - **openFile(path)**: normalize; find matching key; openFile(match ?? path).
  - **refreshFileTree**: no-op (tree is reactive).
- **uninstallIdeAPI**: delete window.ideAPI.

### `components/AgentChat.tsx`

- **State**: messages (Message[]), input (string), isRunning (boolean). **Refs**: orchestratorRef (AgentOrchestrator), bottomRef (scroll anchor).
- **Effect**: Create AgentOrchestrator with callback that appends incoming message to messages. **Effect**: On messages change, scroll bottomRef into view.
- **sendMessage**: If empty or isRunning return; set isRunning; clear input; orchestrator.handleUserMessage(userInput); set isRunning false.
- **getAgentColor / getAgentRole**: Map agent id to Tailwind color and role string.
- **UI**: Agent bar (list of AGENTS with name + role); scrollable message list (empty state “What do you want to build?”); each message shows agent badge (if not user) and bubble (user right, assistant left); ReactMarkdown for content with simple styling (pre, code, ul, ol); “Agents working…” when isRunning; input textarea (placeholder “Ask AI…”), Send button; hint “Enter to send · Shift+Enter new line · @alex @iris to mention”.

**Summary**: User types in AgentChat → Orchestrator routes to Mike (or @agent) → Claude; Mike can delegate via DELEGATE_TO:alex … → Alex runs with tools → tools use window.ideAPI → ide-bridge uses useIDEStore.getState() to read/write files, list files, append terminal, open file. So the Agents chat is fully frontend-driven (Claude + IDE bridge) and does not use the backend pipeline.

---

## 12. Data flow summary

### CLI generate (v2)

```
User: cli.py generate "blog" --production --build
  → handle_generate
    → PipelineRequest(idea, mode, channel=cli, …)
    → run_pipeline(request)  [pipeline_runner]
      → state PLANNING
      → create_execution_plan(idea, mode)  [team_lead_brain]
      → state EXECUTING
      → for each agent in execution_order: get_agent_function(name), run with contract validation, ledger
      → persist artifacts, index memory
      → state COMPLETED
    → if --build: merge_agent_outputs, build_project, write files to --output
```

### Web Atoms (backend pipeline)

```
User in NovaIDE, Atoms tab, sends message
  → AtomsChatPanel calls backend (e.g. /atmos/... or atoms_engine SSE)
  → Backend: AtomsEngine.run(prompt) or equivalent
    → PipelineRequest(idea=prompt, channel=web, …)
    → run_pipeline(...)  [same as CLI]
  → Events streamed to frontend; frontend updates chat, terminal, file tree (via store)
```

### Web Agents (frontend-only multi-agent)

```
User in NovaIDE, Agents tab, types and sends
  → AgentChat.sendMessage
    → AgentOrchestrator.handleUserMessage(input)
      → routeMessage → e.g. mike
      → runAgent("mike", input)
        → Claude API (system=Mike, messages, no tools)
        → processResponse: if DELEGATE_TO:alex … → runAgent("alex", brief)
          → Claude API (system=Alex, messages, tools=IDE_TOOLS)
          → processResponse: if tool_use → executeTool → window.ideAPI.* → ide-bridge → useIDEStore.getState() → fileContents/terminal/openFile/etc.
          → continueAgentWithToolResult → Claude again with tool result
      → addAgentMessage → setMessages in React → UI update
```

### IDE store usage

- **FilePanel**: fileContents, fileStatuses → build tree; openFile on click.
- **EditorPanel / EditorCanvas**: activeFile, fileContents[activeFile], updateFileContent.
- **TerminalPanel**: terminalLines, clearTerminal.
- **AtomsChatPanel**: chatMessages, addChatMessage, terminalLines (for backend output), createFile/appendToFile (when backend sends file updates).
- **ide-bridge**: getState() → readFile/writeFile/listFiles/runCommand/openFile/refreshFileTree implemented with store methods above.

---

## End of analysis

This document covered:

- **Root**: CLI commands and handlers.
- **Backend**: main.py, core (orchestrator, pipeline_runner, contracts, registry), engine (state, atoms_engine, token ledger/governance), agents (team lead brain, execution plan), API routers at a high level.
- **Frontend**: main.tsx, router, NovaIDE layout, ide-store (state and persistence), and the full Agents path (definitions, tools, orchestrator, ide-bridge, AgentChat).
- **Data flows**: CLI generate, web Atoms pipeline, web Agents chat, and how the IDE store is used everywhere.

For more detail on a specific file, open it and use this doc as a map: each section points to the responsible module and the main line ranges or concepts.
