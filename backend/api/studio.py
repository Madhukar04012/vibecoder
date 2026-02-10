"""
VibeCober Studio API
Endpoints for the IDE + AI Team workspace
"""

import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
from pydantic import BaseModel
from typing import Optional, List, Literal, Dict
import os
import subprocess
import asyncio
import json
import re
import atexit
import socket
import time

router = APIRouter(prefix="/studio", tags=["studio"])

# ============== Schemas ==============

class FileNode(BaseModel):
    name: str
    path: str
    type: Literal["file", "folder"]
    children: Optional[List["FileNode"]] = None

class PlanRequest(BaseModel):
    prompt: str

class PlanActions(BaseModel):
    createFiles: List[str] = []
    modifyFiles: List[str] = []
    runCommands: List[str] = []

class PlanSchema(BaseModel):
    summary: str
    actions: PlanActions

class PlanResponse(BaseModel):
    plan: PlanSchema

# Phase 4.2: Diff Agent input/output
class DiffActionReplace(BaseModel):
    type: Literal["replace"] = "replace"
    file: str
    search: str
    replace: str

class DiffActionInsert(BaseModel):
    type: Literal["insert"] = "insert"
    file: str
    after: str
    content: str

class DiffActionDelete(BaseModel):
    type: Literal["delete"] = "delete"
    file: str
    search: str

class DiffPlanSchema(BaseModel):
    summary: str
    diffs: List[dict]  # DiffAction union

class DiffPlanRequest(BaseModel):
    plan: PlanSchema
    files: Dict[str, str]  # path -> content

class DiffPlanResponse(BaseModel):
    diffPlan: DiffPlanSchema

# Engineer Agent (MetaGPT-style: full file content)
class EngineerRequest(BaseModel):
    plan: PlanSchema
    file_path: str

class EngineerResponse(BaseModel):
    file: str
    content: str

class ChatRequest(BaseModel):
    project_id: str
    message: str
    mode: str = "full"

class ChatMessage(BaseModel):
    agent: str
    content: str
    type: Literal["text", "file_change", "error", "system"]
    file_path: Optional[str] = None
    diff: Optional[dict] = None

class ChatResponse(BaseModel):
    messages: List[ChatMessage]
    finished: bool

class ApplyRequest(BaseModel):
    project_id: str
    file_path: str
    content: str

class ApplyResponse(BaseModel):
    success: bool
    file_path: str
    error: Optional[str] = None

class RunRequest(BaseModel):
    project_id: str
    command: Literal["run", "test", "build", "deploy"]

class ExecuteRequest(BaseModel):
    project_id: str
    command: str

class RunResponse(BaseModel):
    success: bool
    output: str
    exit_code: int

class FileContentResponse(BaseModel):
    content: str
    path: str

class DiffResponse(BaseModel):
    before: str
    after: str

class PreviewStartRequest(BaseModel):
    project_id: str

class PreviewStartResponse(BaseModel):
    url: str
    ready: bool
    error: Optional[str] = None

# ============== Preview process storage ==============
_preview_processes: Dict[str, subprocess.Popen] = {}
_preview_ports: Dict[str, int] = {}

PREVIEW_PORT_RANGE = (5174, 5182)


def _find_free_port() -> int:
    """Find first available port in range."""
    for port in range(PREVIEW_PORT_RANGE[0], PREVIEW_PORT_RANGE[1]):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            continue
    return PREVIEW_PORT_RANGE[0]


def _cleanup_preview_processes() -> None:
    """Kill all preview processes (on shutdown)."""
    for project_id, proc in list(_preview_processes.items()):
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        del _preview_processes[project_id]
        _preview_ports.pop(project_id, None)


atexit.register(_cleanup_preview_processes)

# ============== Helper Functions ==============

def get_project_path(project_id: str) -> str:
    """Get the absolute path for a project (demo: uses generated_projects folder)"""
    base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_projects")
    project_path = os.path.join(base_path, project_id)
    return project_path

def build_file_tree(path: str, base_path: str = "") -> List[FileNode]:
    """Build a file tree from a directory"""
    result = []
    try:
        entries = sorted(os.listdir(path))
        # Folders first, then files
        folders = [e for e in entries if os.path.isdir(os.path.join(path, e))]
        files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
        
        for name in folders + files:
            if name.startswith('.') or name == '__pycache__' or name == 'node_modules':
                continue
            
            full_path = os.path.join(path, name)
            rel_path = os.path.join(base_path, name) if base_path else name
            
            if os.path.isdir(full_path):
                children = build_file_tree(full_path, rel_path)
                result.append(FileNode(
                    name=name,
                    path=rel_path,
                    type="folder",
                    children=children
                ))
            else:
                result.append(FileNode(
                    name=name,
                    path=rel_path,
                    type="file"
                ))
    except Exception as e:
        logger.warning("build_file_tree failed for %s: %s", path, e)
    return result


def _run_planner(prompt: str) -> PlanSchema:
    """Run planner: LLM when available, else safe fallback. Never mutates files."""
    try:
        from backend.core.llm_client import call_ollama

        system_prompt = '''You are an architect. Output ONLY a valid JSON object, no other text.
Format:
{"summary":"Brief description of what will be built","actions":{"createFiles":["path/to/file1","path/to/file2"],"modifyFiles":["path/to/existing"],"runCommands":["npm install","npm run build"]}}

Rules:
- summary: One sentence describing the plan
- createFiles: Array of new file paths to create (empty array if none)
- modifyFiles: Array of existing file paths to modify (empty array if none)
- runCommands: Array of shell commands to run (e.g. npm install, npm run dev)
- Only output the JSON object, nothing else'''

        full_prompt = f"{system_prompt}\n\nUser request: {prompt}\n\nJSON:"
        result = call_ollama(full_prompt)

        if result and isinstance(result, dict):
            summary = result.get("summary") or "AI-generated plan"
            acts = result.get("actions") or {}
            create = acts.get("createFiles")
            modify = acts.get("modifyFiles")
            run = acts.get("runCommands")
            if not isinstance(create, list):
                create = []
            if not isinstance(modify, list):
                modify = []
            if not isinstance(run, list):
                run = []
            create = [str(p) for p in create[:50]]
            modify = [str(p) for p in modify[:50]]
            run = [str(c) for c in run[:20]]
            return PlanSchema(
                summary=summary,
                actions=PlanActions(
                    createFiles=create,
                    modifyFiles=modify,
                    runCommands=run,
                ),
            )
    except Exception:
        pass

    return PlanSchema(
        summary=f"Plan for: {prompt[:100]}...",
        actions=PlanActions(
            createFiles=[],
            modifyFiles=[],
            runCommands=["npm install"],
        ),
    )


# ============== Endpoints ==============

@router.post("/plan", response_model=PlanResponse)
async def plan(request: PlanRequest):
    """Phase 2: Planner returns structured intent. No files touched."""
    plan_schema = _run_planner(request.prompt)
    return PlanResponse(plan=plan_schema)


def _run_diff_agent(plan: PlanSchema, files: Dict[str, str]) -> DiffPlanSchema:
    """Phase 4.2: Diff agent produces DiffPlan only. Never mutates files."""
    files_to_modify = plan.actions.modifyFiles or []
    if not files_to_modify:
        return DiffPlanSchema(summary=plan.summary, diffs=[])

    # Build context for LLM
    file_context = []
    for path in files_to_modify[:20]:  # limit scope
        content = files.get(path, "")
        if len(content) > 8000:  # truncate very large files
            content = content[:8000] + "\n// ... (truncated)"
        file_context.append(f"--- FILE: {path} ---\n{content}\n")
    context_block = "\n".join(file_context)

    system_prompt = '''You are a code editor agent.

You receive:
- A plan describing intended changes
- Current file contents

You must output a DiffPlan JSON object:
{"summary":"...","diffs":[{"type":"replace","file":"path","search":"exact text to find","replace":"new text"},{"type":"insert","file":"path","after":"anchor text","content":"lines to insert"},{"type":"delete","file":"path","search":"exact text to remove"}]}

Rules:
- NEVER overwrite entire files
- Use type "replace" for search/replace edits
- Use type "insert" only with a clear "after" anchor from the file
- Use type "delete" to remove existing code
- search/after must be EXACT matches from the file content
- If a safe diff cannot be produced, return {"summary":"...","diffs":[]}
- Output JSON only. No explanation.'''

    user_prompt = f"Plan: {plan.summary}\n\nModify files: {', '.join(files_to_modify)}\n\n{context_block}\n\nJSON:"

    try:
        from backend.core.llm_client import call_ollama
        result = call_ollama(system_prompt + "\n\n" + user_prompt)
        if result and isinstance(result, dict):
            summary = str(result.get("summary", plan.summary))[:500]
            diffs_raw = result.get("diffs")
            if not isinstance(diffs_raw, list):
                return DiffPlanSchema(summary=summary, diffs=[])
            diffs = []
            for d in diffs_raw[:50]:  # limit
                if not isinstance(d, dict):
                    continue
                t = d.get("type")
                f = str(d.get("file", "")).strip()
                if not f:
                    continue
                if t == "replace" and "search" in d and "replace" in d:
                    diffs.append({"type": "replace", "file": f, "search": str(d["search"]), "replace": str(d["replace"])})
                elif t == "insert" and "after" in d and "content" in d:
                    diffs.append({"type": "insert", "file": f, "after": str(d["after"]), "content": str(d["content"])})
                elif t == "delete" and "search" in d:
                    diffs.append({"type": "delete", "file": f, "search": str(d["search"])})
            return DiffPlanSchema(summary=summary, diffs=diffs)
    except Exception:
        pass

    return DiffPlanSchema(summary=plan.summary, diffs=[])


@router.post("/diff-plan", response_model=DiffPlanResponse)
async def diff_plan(request: DiffPlanRequest):
    """Phase 4.2: Diff agent produces DiffPlan. No filesystem mutation."""
    diff_plan_schema = _run_diff_agent(request.plan, request.files)
    return DiffPlanResponse(diffPlan=diff_plan_schema)


def _run_engineer(plan: PlanSchema, file_path: str) -> str:
    """Engineer agent: generate full file content. No filesystem mutation."""
    ext = file_path.split(".")[-1].lower() if "." in file_path else ""
    lang_hint = {
        "py": "Python",
        "ts": "TypeScript",
        "tsx": "TypeScript React",
        "js": "JavaScript",
        "jsx": "JavaScript React",
        "json": "JSON",
        "css": "CSS",
        "html": "HTML",
    }.get(ext, "code")

    system_prompt = f"""You are a senior software engineer.

Your task is to write the COMPLETE contents of a single file.

INPUT YOU WILL RECEIVE:
- A project plan describing the feature and context
- A file path that must be created
- The programming language is inferred from the file extension ({lang_hint})

RULES (STRICT):
- Write PRODUCTION-READY code
- Do NOT include placeholders, TODOs, or pseudocode
- Do NOT explain anything
- Do NOT output markdown
- Do NOT reference MetaGPT or the planning process
- Do NOT assume other files unless implied by the plan
- If configuration is required, include sane defaults
- Follow best practices for the inferred language
- Assume this file will be part of a real project

OUTPUT FORMAT (JSON ONLY):
{{
  "content": "<full file contents with \\n for newlines>"
}}

FAILURE BEHAVIOR:
- If you are unsure, output a minimal but valid implementation
- Never output empty content"""

    user_prompt = f"Plan: {plan.summary}\n\nCreate file: {file_path}\n\nJSON:"

    try:
        from backend.core.llm_client import call_ollama
        result = call_ollama(system_prompt + "\n\n" + user_prompt)
        if result and isinstance(result, dict) and "content" in result:
            raw = result.get("content", "")
            if isinstance(raw, str):
                return raw.replace("\\n", "\n")
    except Exception:
        pass

    return f"# {file_path}\n# Generated placeholder\n# Plan: {plan.summary}\n"


@router.post("/engineer", response_model=EngineerResponse)
async def engineer(request: EngineerRequest):
    """Engineer agent: generate full file content. No filesystem mutation."""
    content = _run_engineer(request.plan, request.file_path)
    return EngineerResponse(file=request.file_path, content=content)


@router.get("/project/{project_id}", response_model=List[FileNode])
async def get_project(project_id: str):
    """Get project file tree"""
    project_path = get_project_path(project_id)
    
    if not os.path.exists(project_path):
        # Return demo structure for non-existent projects
        return [
            FileNode(name="backend", path="backend", type="folder", children=[
                FileNode(name="main.py", path="backend/main.py", type="file"),
                FileNode(name="auth", path="backend/auth", type="folder", children=[
                    FileNode(name="routes.py", path="backend/auth/routes.py", type="file"),
                    FileNode(name="jwt.py", path="backend/auth/jwt.py", type="file"),
                ]),
                FileNode(name="models", path="backend/models", type="folder", children=[
                    FileNode(name="user.py", path="backend/models/user.py", type="file"),
                ]),
            ]),
            FileNode(name="tests", path="tests", type="folder", children=[
                FileNode(name="test_auth.py", path="tests/test_auth.py", type="file"),
            ]),
            FileNode(name="requirements.txt", path="requirements.txt", type="file"),
            FileNode(name="Dockerfile", path="Dockerfile", type="file"),
        ]
    
    return build_file_tree(project_path)

@router.get("/file", response_model=FileContentResponse)
async def get_file(project_id: str, path: str):
    """Get file content"""
    project_path = get_project_path(project_id)
    file_path = os.path.join(project_path, path)
    
    # Demo content for non-existent files
    demo_contents = {
        "backend/main.py": '''from fastapi import FastAPI
from backend.auth.routes import router as auth_router

app = FastAPI(title="Generated API")

app.include_router(auth_router, prefix="/auth")

@app.get("/")
def root():
    return {"message": "Welcome to the API"}
''',
        "backend/auth/routes.py": '''from fastapi import APIRouter, Depends
from backend.auth.jwt import verify_token

router = APIRouter()

@router.post("/login")
def login(email: str, password: str):
    # TODO: Implement login logic
    return {"token": "jwt_token_here"}

@router.get("/me")
def get_current_user(token: str = Depends(verify_token)):
    return {"user": "current_user"}
''',
        "backend/auth/jwt.py": '''from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def create_token(data: dict):
    expire = datetime.utcnow() + timedelta(hours=24)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
''',
        "backend/models/user.py": '''from sqlalchemy import Column, Integer, String
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
''',
        "tests/test_auth.py": '''import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_login():
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200

def test_get_me():
    response = client.get("/auth/me")
    assert response.status_code in [200, 401]
''',
        "requirements.txt": '''fastapi==0.109.0
uvicorn==0.24.0
sqlalchemy==2.0.23
python-jose==3.3.0
bcrypt==4.1.2
''',
        "Dockerfile": '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
    }
    
    if not os.path.exists(file_path):
        content = demo_contents.get(path, f"// File: {path}\n// Content not found")
        return FileContentResponse(content=content, path=path)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return FileContentResponse(content=content, path=path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the AI team and get responses"""
    from backend.core.llm_client import nim_chat, ollama_chat

    prompt = f"You are a helpful coding assistant. The user said: {request.message}\n\nRespond briefly and helpfully."

    # 1. Try NVIDIA NIM (user's API key)
    reply = nim_chat(prompt)

    # 2. Fallback to Ollama
    if not reply:
        reply = ollama_chat(prompt)

    if reply:
        return ChatResponse(
            messages=[ChatMessage(agent="assistant", content=reply, type="text")],
            finished=True
        )

    # 3. Fallback when no AI available
    return ChatResponse(
        messages=[ChatMessage(
            agent="assistant",
            content=f"Sure! You said: \"{request.message}\". (Set NIM_API_KEY in .env for AI replies.)",
            type="text"
        )],
        finished=True
    )

@router.post("/apply", response_model=ApplyResponse)
async def apply_change(request: ApplyRequest):
    """Apply a file change (create or overwrite)"""
    project_path = get_project_path(request.project_id)
    file_path = os.path.join(project_path, request.file_path)
    
    try:
        # Create directory if needed
        parent = os.path.dirname(file_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(request.content)
        
        return ApplyResponse(success=True, file_path=request.file_path)
    except Exception as e:
        return ApplyResponse(success=False, file_path=request.file_path, error=str(e))

@router.post("/run", response_model=RunResponse)
async def run_command(request: RunRequest):
    """Run a project command"""
    project_path = get_project_path(request.project_id)
    
    command_map = {
        "run": "python -m uvicorn backend.main:app --reload",
        "test": "python -m pytest tests/ -v",
        "build": "pip install -r requirements.txt",
        "deploy": "echo 'Deploy not configured'",
    }
    
    cmd = command_map.get(request.command, "echo 'Unknown command'")
    
    try:
        # For demo purposes, return simulated output
        simulated_outputs = {
            "run": "INFO: Uvicorn running on http://127.0.0.1:8000\nINFO: Started reloader process",
            "test": "tests/test_auth.py::test_login PASSED\ntests/test_auth.py::test_get_me PASSED\n\n2 passed in 0.5s",
            "build": "Successfully installed fastapi-0.109.0 uvicorn-0.24.0 sqlalchemy-2.0.23",
            "deploy": "Deployment started...\nBuilding container...\nPushing to registry...\nDeploy complete!",
        }
        
        return RunResponse(
            success=True,
            output=simulated_outputs.get(request.command, "Command executed"),
            exit_code=0
        )
    except Exception as e:
        return RunResponse(success=False, output=str(e), exit_code=1)


@router.post("/execute", response_model=RunResponse)
async def execute_command(request: ExecuteRequest):
    """Phase 3: Run arbitrary command in project directory (e.g. npm install, npm run build)"""
    project_path = get_project_path(request.project_id)
    os.makedirs(project_path, exist_ok=True)

    try:
        result = subprocess.run(
            request.command,
            shell=True,
            cwd=project_path,
            capture_output=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        output = (stdout + "\n" + stderr).strip() or "(no output)"
        return RunResponse(
            success=result.returncode == 0,
            output=output,
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return RunResponse(success=False, output="Command timed out", exit_code=124)
    except Exception as e:
        return RunResponse(success=False, output=str(e), exit_code=1)

@router.get("/diff", response_model=DiffResponse)
async def get_diff(project_id: str, path: str):
    """Get diff for a pending change"""
    # For demo, return simulated diff
    return DiffResponse(
        before=f"# Original {path}\n# Previous implementation",
        after=f"# Modified {path}\n# New implementation with requested changes"
    )


def _start_preview_process(project_path: str, port: int, is_node: bool, backend_main: bool = False) -> subprocess.Popen:
    """Start preview process. Returns Popen instance."""
    if is_node:
        return subprocess.Popen(
            ["npm", "run", "dev", "--", "--port", str(port)],
            cwd=project_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=os.name == "nt",
        )
    if backend_main:
        return subprocess.Popen(
            ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", str(port)],
            cwd=project_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=os.name == "nt",
        )
    return subprocess.Popen(
        ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(port)],
        cwd=project_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=os.name == "nt",
    )


@router.post("/preview/start", response_model=PreviewStartResponse)
async def preview_start(request: PreviewStartRequest):
    """Start dev server for project preview. Returns URL when ready."""
    project_id = request.project_id
    project_path = get_project_path(project_id)

    # Kill existing process for this project
    if project_id in _preview_processes:
        try:
            _preview_processes[project_id].terminate()
            _preview_processes[project_id].wait(timeout=3)
        except Exception:
            try:
                _preview_processes[project_id].kill()
            except Exception:
                pass
        del _preview_processes[project_id]
        _preview_ports.pop(project_id, None)

    if not os.path.exists(project_path):
        return PreviewStartResponse(url="http://127.0.0.1:5174", ready=False, error="Project not found")

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    pkg_json = os.path.join(project_path, "package.json")
    if os.path.isfile(pkg_json):
        # Run npm install (with timeout + error capture)
        try:
            result = subprocess.run(
                ["npm", "install"],
                cwd=project_path,
                capture_output=True,
                timeout=120,
                shell=os.name == "nt",
                text=True,
            )
            if result.returncode != 0 and result.stderr:
                return PreviewStartResponse(
                    url=base_url,
                    ready=False,
                    error=f"npm install failed: {result.stderr[:200]}",
                )
        except subprocess.TimeoutExpired:
            return PreviewStartResponse(url=base_url, ready=False, error="npm install timed out")
        except Exception as e:
            return PreviewStartResponse(url=base_url, ready=False, error=str(e))

        proc = _start_preview_process(project_path, port, is_node=True)
    else:
        main_py = os.path.join(project_path, "main.py")
        backend_main = os.path.join(project_path, "backend", "main.py")
        if os.path.isfile(main_py):
            proc = _start_preview_process(project_path, port, is_node=False, backend_main=False)
        elif os.path.isfile(backend_main):
            proc = _start_preview_process(project_path, port, is_node=False, backend_main=True)
        else:
            return PreviewStartResponse(url=base_url, ready=False, error="No runnable project (package.json or main.py)")

    _preview_processes[project_id] = proc
    _preview_ports[project_id] = port

    # Crash recovery: check process is alive after short delay
    time.sleep(0.5)
    if proc.poll() is not None:
        _preview_processes.pop(project_id, None)
        _preview_ports.pop(project_id, None)
        return PreviewStartResponse(
            url=base_url,
            ready=False,
            error=f"Preview process exited (code {proc.returncode})",
        )

    return PreviewStartResponse(url=base_url, ready=True)
