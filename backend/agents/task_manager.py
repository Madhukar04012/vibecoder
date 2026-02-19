"""
TaskManagerAgent - Converts approved ProjectPlan into executable Tasks.

Responsibility:
- Takes an approved ProjectPlan
- Generates a list of tasks (AI or fallback)
- Assigns suggested agents
- Writes tasks to DB
- Guarantees output (never blocks)

Does NOT:
- Handle API logic
- Create DB sessions
- Handle user auth
- Handle UI logic
"""

from typing import List
import json

from sqlalchemy.orm import Session

from backend.models.task import Task
from backend.models.project_plan import ProjectPlan
from backend.models.enums import TaskPriority, TaskStatus, AgentRole
from backend.core.llm_client import call_llm


class TaskManagerAgent:
    """
    Responsible for converting an approved ProjectPlan
    into executable Tasks.

    AI-first with deterministic fallback.
    """

    def __init__(self, db: Session):
        self.db = db

    def run(self, project_id: str, plan: ProjectPlan) -> List[Task]:
        """
        Entry point called after plan approval.
        Returns list of created Task objects.
        """
        try:
            tasks_data = self._generate_tasks_with_ai(plan)
        except Exception as e:
            print(f"[TaskManager] AI failed: {e}. Using fallback.")
            tasks_data = self._fallback_tasks(plan)

        tasks = self._persist_tasks(project_id, tasks_data)
        return tasks

    # ---------- AI PATH ----------

    def _generate_tasks_with_ai(self, plan: ProjectPlan) -> List[dict]:
        """
        Uses LLM to convert plan → tasks.
        Must return structured data.
        """
        # Parse the architecture JSON from the plan
        try:
            architecture = json.loads(plan.architecture_json)
        except json.JSONDecodeError:
            architecture = {"summary": "Unknown project"}

        prompt = f"""You are a senior technical project manager.

Given this project plan, generate a list of development tasks.
Each task must include:
- title (string)
- description (string)
- priority (one of: low, medium, high)
- assigned_agent (one of: team_lead, backend_engineer, frontend_engineer, database_engineer, qa_engineer)

Return ONLY a valid JSON array. No explanation, just JSON.

Project Architecture:
{json.dumps(architecture, indent=2)}
"""

        response = call_llm(prompt)
        
        if response is None:
            raise ValueError("Empty AI response")

        # call_llm returns parsed JSON when possible, but we need to handle array format
        tasks = self._parse_llm_response(response)

        if not tasks:
            raise ValueError("Empty AI task list")

        return tasks

    def _parse_llm_response(self, response) -> List[dict]:
        """
        Parse LLM response into task list.
        Handles both direct list and dict with tasks key.
        """
        # If call_llm already parsed as list
        if isinstance(response, list):
            return response
        
        # If it's a dict, look for tasks key
        if isinstance(response, dict):
            if "tasks" in response:
                return response["tasks"]
            # Maybe it's a single task dict?
            if "title" in response:
                return [response]
        
        # Try to parse as JSON string (fallback)
        if isinstance(response, str):
            try:
                data = json.loads(response)
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass
        
        return []

    # ---------- FALLBACK PATH ----------

    def _fallback_tasks(self, plan: ProjectPlan) -> List[dict]:
        """
        Deterministic, guaranteed-safe task generation.
        Works even if AI is completely unavailable.
        """
        return [
            {
                "title": "Initialize backend project",
                "description": "Setup FastAPI app structure and base configuration",
                "priority": TaskPriority.HIGH,
                "assigned_agent": AgentRole.BACKEND_ENGINEER,
            },
            {
                "title": "Setup database models",
                "description": "Define SQLAlchemy models and relationships",
                "priority": TaskPriority.HIGH,
                "assigned_agent": AgentRole.DATABASE_ENGINEER,
            },
            {
                "title": "Implement authentication",
                "description": "JWT auth, login, signup, protected routes",
                "priority": TaskPriority.HIGH,
                "assigned_agent": AgentRole.BACKEND_ENGINEER,
            },
            {
                "title": "Create frontend layout",
                "description": "Initialize React app and basic layout components",
                "priority": TaskPriority.MEDIUM,
                "assigned_agent": AgentRole.FRONTEND_ENGINEER,
            },
            {
                "title": "Add basic tests",
                "description": "Health check and core API tests",
                "priority": TaskPriority.MEDIUM,
                "assigned_agent": AgentRole.QA_ENGINEER,
            },
        ]

    # ---------- PERSISTENCE ----------

    def _persist_tasks(self, project_id: str, tasks_data: List[dict]) -> List[Task]:
        """
        Write tasks to database.
        Handles both enum objects and string values.
        """
        tasks: List[Task] = []

        for item in tasks_data:
            # Handle priority - could be string or enum
            priority = item.get("priority", TaskPriority.MEDIUM)
            if isinstance(priority, str):
                priority = TaskPriority(priority.lower())

            # Handle assigned_agent - could be string or enum
            assigned_agent = item.get("assigned_agent")
            if isinstance(assigned_agent, str):
                try:
                    assigned_agent = AgentRole(assigned_agent.lower())
                except ValueError:
                    assigned_agent = None

            task = Task(
                title=item["title"],
                description=item.get("description"),
                priority=priority,
                status=TaskStatus.TODO,
                assigned_agent=assigned_agent,
                project_id=project_id,
            )
            self.db.add(task)
            tasks.append(task)

        self.db.commit()

        # Refresh to get IDs
        for task in tasks:
            self.db.refresh(task)

        return tasks
