"""
VibeCober Studio API
Endpoints for the IDE + AI Team workspace
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Literal
import os
import subprocess
import asyncio

router = APIRouter(prefix="/studio", tags=["studio"])

# ============== Schemas ==============

class FileNode(BaseModel):
    name: str
    path: str
    type: Literal["file", "folder"]
    children: Optional[List["FileNode"]] = None

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
        pass
    return result

# ============== Endpoints ==============

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
    messages = []
    
    # Simulate Team Lead response
    messages.append(ChatMessage(
        agent="team_lead",
        content=f"I understand you want to: \"{request.message}\"\n\nLet me create a plan for the team.",
        type="text"
    ))
    
    # Simulate Planner response
    messages.append(ChatMessage(
        agent="planner",
        content="Creating execution plan:\n\n1. Analyze requirements\n2. Design architecture\n3. Implement changes\n4. Run tests\n5. Validate results",
        type="text"
    ))
    
    # Simulate Coder response with file change
    if "auth" in request.message.lower() or "login" in request.message.lower():
        messages.append(ChatMessage(
            agent="coder",
            content="I will implement authentication. Modifying:",
            type="text"
        ))
        messages.append(ChatMessage(
            agent="coder",
            content="backend/auth/routes.py",
            type="file_change",
            file_path="backend/auth/routes.py",
            diff={
                "before": "# Old auth code",
                "after": "# New auth code with your requested changes"
            }
        ))
    else:
        messages.append(ChatMessage(
            agent="coder",
            content="I will implement the requested changes.",
            type="text"
        ))
    
    # Simulate Tester response
    messages.append(ChatMessage(
        agent="tester",
        content="I've added test cases for the new functionality. All tests passing.",
        type="text"
    ))
    
    return ChatResponse(messages=messages, finished=True)

@router.post("/apply", response_model=ApplyResponse)
async def apply_change(request: ApplyRequest):
    """Apply a file change"""
    project_path = get_project_path(request.project_id)
    file_path = os.path.join(project_path, request.file_path)
    
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
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

@router.get("/diff", response_model=DiffResponse)
async def get_diff(project_id: str, path: str):
    """Get diff for a pending change"""
    # For demo, return simulated diff
    return DiffResponse(
        before=f"# Original {path}\n# Previous implementation",
        after=f"# Modified {path}\n# New implementation with requested changes"
    )
