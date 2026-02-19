"""
Backend Engineer Agent - Executes backend-related tasks.

Responsibility:
- Pick next available backend task
- Execute the task (generate code, create files)
- Update task status in DB
- Return execution result

This is the first Engineer Agent - pattern for Frontend, DB, QA agents.
"""

from typing import Optional, Dict, Any
import json

from sqlalchemy.orm import Session

from backend.models.task import Task
from backend.models.project import Project
from backend.models.project_plan import ProjectPlan
from backend.models.execution_log import ExecutionLog
from backend.models.enums import TaskStatus, AgentRole
from backend.generator.project_builder import build_project
from backend.templates.code_templates import get_templates


class BackendEngineerAgent:
    """
    Executes backend tasks for a project.
    AI-capable with deterministic fallback.
    """

    def __init__(self, db: Session):
        self.db = db
        self.role = AgentRole.BACKEND_ENGINEER

    def run_next_task(self, project_id: str) -> Dict[str, Any]:
        """
        Find and execute the next available backend task.
        Returns execution result.
        """
        # 1. Find next TODO task assigned to backend
        task = self._get_next_task(project_id)
        
        if not task:
            return {
                "status": "no_tasks",
                "message": "No pending backend tasks found"
            }
        
        # 2. Mark task as in_progress
        task.status = TaskStatus.IN_PROGRESS
        self.db.commit()
        
        try:
            # 3. Execute the task
            result = self._execute_task(project_id, task)
            
            # 4. Mark task as done
            task.status = TaskStatus.DONE
            
            # 5. Log successful execution
            log = ExecutionLog(
                task_id=task.id,
                project_id=project_id,
                agent="backend_engineer",
                status="success",
                message=f"Task '{task.title}' executed successfully",
                files_created=result.get("files_created", 0),
                output_dir=result.get("output_dir", "")
            )
            self.db.add(log)
            self.db.commit()
            
            return {
                "status": "completed",
                "task_id": task.id,
                "task_title": task.title,
                "result": result
            }
            
        except Exception as e:
            # Rollback to TODO on failure
            task.status = TaskStatus.TODO
            
            # Log failed execution
            log = ExecutionLog(
                task_id=task.id,
                project_id=project_id,
                agent="backend_engineer",
                status="failure",
                message=str(e),
                files_created=0
            )
            self.db.add(log)
            self.db.commit()
            
            return {
                "status": "failed",
                "task_id": task.id,
                "task_title": task.title,
                "error": str(e)
            }

    def _get_next_task(self, project_id: str) -> Optional[Task]:
        """
        Get next pending backend task for the project.
        Ordered by priority (high first) then creation time.
        """
        return (
            self.db.query(Task)
            .filter(
                Task.project_id == project_id,
                Task.assigned_agent == AgentRole.BACKEND_ENGINEER,
                Task.status == TaskStatus.TODO
            )
            .order_by(Task.priority.desc(), Task.created_at.asc())
            .first()
        )

    def _execute_task(self, project_id: str, task: Task) -> Dict[str, Any]:
        """
        Execute the actual task.
        For now: deterministic code generation based on task title.
        """
        # Get project info
        project = self.db.query(Project).filter(Project.id == project_id).first()
        
        # Get plan for architecture context
        plan = self.db.query(ProjectPlan).filter(
            ProjectPlan.project_id == project_id
        ).first()
        
        architecture = {}
        if plan and plan.architecture_json:
            try:
                architecture = json.loads(plan.architecture_json)
            except json.JSONDecodeError:
                architecture = {}
        
        # Map task to code generation
        task_lower = task.title.lower()
        
        if "backend" in task_lower or "fastapi" in task_lower or "initialize" in task_lower:
            return self._generate_backend_setup(project_id, architecture)
        elif "auth" in task_lower or "authentication" in task_lower:
            return self._generate_auth_code(project_id)
        elif "api" in task_lower or "endpoint" in task_lower:
            return self._generate_api_routes(project_id, architecture)
        else:
            # Generic backend task
            return self._generate_generic_module(project_id, task.title)

    def _generate_backend_setup(self, project_id: str, architecture: dict) -> Dict[str, Any]:
        """Generate S-class FastAPI project structure."""
        project_name = f"project_{project_id[:8]}"
        
        # Try S-class templates first
        try:
            from backend.templates.sclass_templates import get_sclass_backend_templates
            sclass_files = get_sclass_backend_templates()
            
            # Organize into nested structure
            backend = {}
            for path, content in sclass_files.items():
                parts = path.replace("\\", "/").split("/")
                current = backend
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = content
            
            structure = {project_name: {"backend": backend}}
            result = build_project(structure, f"./generated/{project_id}")
            return {
                "action": "backend_setup_sclass",
                "files_created": result.get("total_files", 0),
                "output_dir": result.get("output_dir", ""),
                "quality": result.get("quality", {}),
            }
        except ImportError:
            pass
        
        # Fallback to legacy templates
        structure = {
            project_name: {
                "backend": {
                    "main.py": self._fastapi_main_template(),
                    "requirements.txt": "fastapi\nuvicorn\n",
                    "__init__.py": "",
                }
            }
        }
        
        result = build_project(structure, f"./generated/{project_id}")
        return {
            "action": "backend_setup",
            "files_created": result.get("total_files", 0),
            "output_dir": result.get("output_dir", "")
        }

    def _generate_auth_code(self, project_id: str) -> Dict[str, Any]:
        """Generate authentication module."""
        project_name = f"project_{project_id[:8]}"
        
        structure = {
            project_name: {
                "backend": {
                    "auth": {
                        "__init__.py": "",
                        "jwt.py": self._jwt_template(),
                        "routes.py": self._auth_routes_template(),
                    }
                }
            }
        }
        
        result = build_project(structure, f"./generated/{project_id}")
        return {
            "action": "auth_module",
            "files_created": result.get("total_files", 0),
            "output_dir": result.get("output_dir", "")
        }

    def _generate_api_routes(self, project_id: str, architecture: dict) -> Dict[str, Any]:
        """Generate API routes based on architecture modules."""
        project_name = f"project_{project_id[:8]}"
        
        modules = architecture.get("modules", ["users", "items"])
        routes_content = self._api_routes_template(modules)
        
        structure = {
            project_name: {
                "backend": {
                    "api": {
                        "__init__.py": "",
                        "routes.py": routes_content,
                    }
                }
            }
        }
        
        result = build_project(structure, f"./generated/{project_id}")
        return {
            "action": "api_routes",
            "modules": modules,
            "files_created": result.get("total_files", 0),
            "output_dir": result.get("output_dir", "")
        }

    def _generate_generic_module(self, project_id: str, task_title: str) -> Dict[str, Any]:
        """Generate a generic module based on task title."""
        module_name = task_title.lower().replace(" ", "_")[:20]
        project_name = f"project_{project_id[:8]}"
        
        structure = {
            project_name: {
                "backend": {
                    module_name: {
                        "__init__.py": f"# {task_title} module\n",
                    }
                }
            }
        }
        
        result = build_project(structure, f"./generated/{project_id}")
        return {
            "action": "generic_module",
            "module": module_name,
            "files_created": result.get("total_files", 0),
            "output_dir": result.get("output_dir", "")
        }

    # ========== Code Templates ==========
    
    def _fastapi_main_template(self) -> str:
        return '''"""
FastAPI Application - Generated by VibeCober
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Generated API",
    description="API generated by VibeCober",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "running", "message": "API is live"}

@app.get("/health")
def health():
    return {"status": "healthy"}
'''

    def _jwt_template(self) -> str:
        return '''"""
JWT Authentication - Generated by VibeCober
"""

from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
'''

    def _auth_routes_template(self) -> str:
        return '''"""
Auth Routes - Generated by VibeCober
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(request: LoginRequest):
    # TODO: Implement actual authentication
    return {"access_token": "token", "token_type": "bearer"}

@router.post("/register")
def register(request: LoginRequest):
    # TODO: Implement user registration
    return {"message": "User registered"}
'''

    def _api_routes_template(self, modules: list) -> str:
        routes = [f'# Routes for: {", ".join(modules)}']
        routes.append('''
from fastapi import APIRouter

router = APIRouter()
''')
        for module in modules:
            routes.append(f'''
@router.get("/{module}")
def list_{module}():
    return {{"items": [], "module": "{module}"}}
''')
        return "\n".join(routes)
