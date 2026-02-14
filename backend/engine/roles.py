"""
Concrete Role Implementations

MetaGPT-style roles for the software development team.
Each role has specific responsibilities and actions.
"""

from typing import Any, Dict, List
from backend.engine.role import Role, Action, Message, RoleState, UserRequirement


# ─── Team Leader ──────────────────────────────────────────────────────────────

class AnalyzeRequirement(Action):
    """Analyze user requirement and create execution plan."""
    name = "analyze_requirement"
    description = "Analyze requirements and assign work"
    
    async def run(self, requirement: str = "") -> Dict[str, Any]:
        return {
            "analysis": "Requirement analyzed",
            "agents_needed": ["product_manager", "architect", "engineer", "qa_engineer"],
        }


class TeamLeader(Role):
    """
    Team Leader - Coordinates the team.
    
    Watches: user_requirement
    Actions: AnalyzeRequirement
    """
    name = "team_leader"
    profile = "Team Leader"
    goal = "Coordinate the team and ensure project success"
    constraints = "Delegate appropriately, don't micromanage"
    icon = "crown"
    color = "#f59e0b"
    
    def __init__(self):
        super().__init__()
        self.set_actions([AnalyzeRequirement])
        self._watch([UserRequirement])


# ─── Product Manager ──────────────────────────────────────────────────────────

class WritePRDAction(Action):
    """Write Product Requirements Document."""
    name = "write_prd"
    description = "Create comprehensive PRD"
    
    async def run(self, *args, **kwargs) -> Dict[str, Any]:
        # In real implementation, this calls the LLM
        return {
            "title": "Project",
            "features": [],
            "user_stories": [],
        }


class ProductManagerRole(Role):
    """
    Product Manager - Defines what to build.
    
    Watches: user_requirement, analyze_requirement
    Actions: WritePRD
    """
    name = "product_manager"
    profile = "Product Manager"
    goal = "Create clear, comprehensive requirements"
    constraints = "Focus on user needs, be specific"
    icon = "clipboard-list"
    color = "#8b5cf6"
    
    def __init__(self):
        super().__init__()
        self.set_actions([WritePRDAction])
        self._watch([UserRequirement, AnalyzeRequirement])


# ─── Architect ────────────────────────────────────────────────────────────────

class WriteDesignAction(Action):
    """Write system architecture design."""
    name = "write_design"
    description = "Create system architecture"
    
    async def run(self, *args, **kwargs) -> Dict[str, Any]:
        return {
            "architecture": "Clean Architecture",
            "stack": {},
            "directory_structure": [],
        }


class ArchitectRole(Role):
    """
    Architect - Designs the system.
    
    Watches: write_prd
    Actions: WriteDesign
    """
    name = "architect"
    profile = "Software Architect"
    goal = "Design scalable, maintainable systems"
    constraints = "Follow best practices, consider trade-offs"
    icon = "layers"
    color = "#06b6d4"
    
    def __init__(self):
        super().__init__()
        self.set_actions([WriteDesignAction])
        self._watch([WritePRDAction])


# ─── Project Manager ──────────────────────────────────────────────────────────

class CreateTasksAction(Action):
    """Break design into tasks."""
    name = "create_tasks"
    description = "Create implementation tasks"
    
    async def run(self, *args, **kwargs) -> List[Dict[str, Any]]:
        return []


class ProjectManagerRole(Role):
    """
    Project Manager - Breaks work into tasks.
    
    Watches: write_design
    Actions: CreateTasks
    """
    name = "project_manager"
    profile = "Project Manager"
    goal = "Break work into manageable tasks"
    constraints = "Prioritize effectively, track progress"
    icon = "kanban"
    color = "#ec4899"
    
    def __init__(self):
        super().__init__()
        self.set_actions([CreateTasksAction])
        self._watch([WriteDesignAction])


# ─── Engineer ─────────────────────────────────────────────────────────────────

class WriteCodeAction(Action):
    """Write implementation code."""
    name = "write_code"
    description = "Write production code"
    
    async def run(self, *args, **kwargs) -> str:
        return ""


class EngineerRole(Role):
    """
    Software Engineer - Writes code.
    
    Watches: write_design, create_tasks
    Actions: WriteCode
    """
    name = "engineer"
    profile = "Software Engineer"
    goal = "Write clean, working code"
    constraints = "Follow design, write tests"
    icon = "code-2"
    color = "#22c55e"
    
    def __init__(self):
        super().__init__()
        self.set_actions([WriteCodeAction])
        self._watch([WriteDesignAction, CreateTasksAction])


# ─── QA Engineer ──────────────────────────────────────────────────────────────

class WriteTestsAction(Action):
    """Write test cases."""
    name = "write_tests"
    description = "Write comprehensive tests"
    
    async def run(self, *args, **kwargs) -> str:
        return ""


class ReviewCodeAction(Action):
    """Review code for quality."""
    name = "review_code"
    description = "Review code quality"
    
    async def run(self, *args, **kwargs) -> Dict[str, Any]:
        return {"approved": True, "issues": []}


class QAEngineerRole(Role):
    """
    QA Engineer - Tests and reviews.
    
    Watches: write_code
    Actions: WriteTests, ReviewCode
    """
    name = "qa_engineer"
    profile = "QA Engineer"
    goal = "Ensure code quality and correctness"
    constraints = "Be thorough, catch edge cases"
    icon = "shield-check"
    color = "#f97316"
    
    def __init__(self):
        super().__init__()
        self.set_actions([WriteTestsAction, ReviewCodeAction])
        self._watch([WriteCodeAction])


# ─── DevOps ───────────────────────────────────────────────────────────────────

class WriteDeploymentAction(Action):
    """Write deployment configuration."""
    name = "write_deployment"
    description = "Create deployment config"
    
    async def run(self, *args, **kwargs) -> Dict[str, str]:
        return {}


class DevOpsRole(Role):
    """
    DevOps Engineer - Handles deployment.
    
    Watches: write_code, review_code
    Actions: WriteDeployment
    """
    name = "devops"
    profile = "DevOps Engineer"
    goal = "Ensure reliable deployment"
    constraints = "Automate, ensure security"
    icon = "rocket"
    color = "#ef4444"
    
    def __init__(self):
        super().__init__()
        self.set_actions([WriteDeploymentAction])
        self._watch([WriteCodeAction, ReviewCodeAction])


# ─── Role Registry ────────────────────────────────────────────────────────────

ROLE_REGISTRY = {
    "team_leader": TeamLeader,
    "product_manager": ProductManagerRole,
    "architect": ArchitectRole,
    "project_manager": ProjectManagerRole,
    "engineer": EngineerRole,
    "qa_engineer": QAEngineerRole,
    "devops": DevOpsRole,
}


def get_all_roles() -> List[Role]:
    """Create instances of all roles."""
    return [cls() for cls in ROLE_REGISTRY.values()]


def get_role_info() -> List[Dict[str, Any]]:
    """Get info about all available roles."""
    return [
        {
            "name": cls.name,
            "profile": cls.profile,
            "goal": cls.goal,
            "icon": cls.icon,
            "color": cls.color,
        }
        for cls in ROLE_REGISTRY.values()
    ]
