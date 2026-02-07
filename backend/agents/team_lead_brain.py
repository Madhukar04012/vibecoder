"""
Team Lead Brain - VibeCober's Decision Engine

This is the BRAIN that decides:
- Which agents should run
- In what order
- With what configuration

Does NOT execute agents. Only outputs JSON execution plans.
"""

from typing import List, Dict, Literal
from pydantic import BaseModel
from enum import Enum


# ========== TYPES ==========

class ProjectType(str, Enum):
    SAAS = "saas"
    CRUD = "crud"
    API = "api"
    DASHBOARD = "dashboard"
    AI_APP = "ai_app"
    LANDING_PAGE = "landing_page"


class Complexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class ProjectAnalysis(BaseModel):
    project_type: ProjectType
    complexity: Complexity
    needs_auth: bool
    needs_database: bool
    needs_tests: bool
    needs_deployment: bool
    risk_level: Literal["low", "medium", "high"]


class ExecutionConfig(BaseModel):
    skip_tests: bool = False
    strict_mode: bool = True
    depth: Literal["minimal", "standard", "full"] = "standard"


class ExecutionPlan(BaseModel):
    """The JSON output that orchestrator will execute"""
    project_type: str
    complexity: str
    agents: List[str]
    execution_order: List[str]
    config: ExecutionConfig


# ========== BRAIN LOGIC ==========

class TeamLeadBrain:
    """
    The decision-making brain of VibeCober.
    Pure logic. No AI calls. Deterministic.
    """
    
    # Available agents (will be expanded as we build more)
    AVAILABLE_AGENTS = {
        "planner",
        "db_schema",
        "auth",
        "coder",
        "tester",
        "deployer"
    }
    
    # Agent dependencies (what must run before what)
    AGENT_DEPENDENCIES = {
        "planner": [],
        "db_schema": ["planner"],
        "auth": ["db_schema"],  # Auth needs db_schema (user table)
        "coder": ["planner"],
        "tester": ["coder"],
        "deployer": ["tester"]
    }
    
    def __init__(self, mode: Literal["simple", "full", "production"] = "full"):
        self.mode = mode
    
    def decide(self, user_idea: str) -> ExecutionPlan:
        """
        Main entry point. Analyzes idea and returns execution plan.
        
        Args:
            user_idea: User's project description
            
        Returns:
            ExecutionPlan: JSON-serializable plan for orchestrator
        """
        # Step 1: Analyze the project
        analysis = self.analyze_project(user_idea)
        
        # Step 2: Select agents based on analysis and mode
        selected_agents = self.select_agents(analysis)
        
        # Step 3: Create execution order respecting dependencies
        execution_order = self.create_execution_order(selected_agents)
        
        # Step 4: Create config
        config = self.create_config(analysis)
        
        # Step 5: Build final plan
        return ExecutionPlan(
            project_type=analysis.project_type.value,
            complexity=analysis.complexity.value,
            agents=selected_agents,
            execution_order=execution_order,
            config=config
        )
    
    def analyze_project(self, idea: str) -> ProjectAnalysis:
        """
        Analyze project idea to determine type, complexity, and needs.
        Deterministic keyword-based analysis.
        """
        idea_lower = idea.lower()
        
        # Determine project type
        if any(word in idea_lower for word in ["saas", "subscription", "payment"]):
            project_type = ProjectType.SAAS
        elif any(word in idea_lower for word in ["api", "rest", "graphql", "endpoint"]):
            project_type = ProjectType.API
        elif any(word in idea_lower for word in ["dashboard", "admin", "analytics"]):
            project_type = ProjectType.DASHBOARD
        elif any(word in idea_lower for word in ["ai", "ml", "llm", "chatbot"]):
            project_type = ProjectType.AI_APP
        elif any(word in idea_lower for word in ["landing", "marketing", "website"]):
            project_type = ProjectType.LANDING_PAGE
        else:
            project_type = ProjectType.CRUD
        
        # Determine complexity (based on keyword count and features)
        complexity_score = 0
        complexity_keywords = [
            "auth", "payment", "email", "notification", "real-time",
            "websocket", "chat", "video", "image", "upload",
            "search", "analytics", "dashboard", "admin"
        ]
        complexity_score = sum(1 for kw in complexity_keywords if kw in idea_lower)
        
        if complexity_score <= 2:
            complexity = Complexity.SIMPLE
        elif complexity_score <= 5:
            complexity = Complexity.MEDIUM
        else:
            complexity = Complexity.COMPLEX
        
        # Determine needs
        needs_auth = any(word in idea_lower for word in [
            "auth", "login", "signup", "user", "account", "password"
        ])
        
        needs_database = any(word in idea_lower for word in [
            "data", "store", "save", "database", "user", "post", "item"
        ]) or project_type != ProjectType.LANDING_PAGE
        
        needs_tests = complexity != Complexity.SIMPLE or self.mode == "production"
        
        needs_deployment = self.mode == "production"
        
        # Risk level
        if project_type == ProjectType.SAAS or "payment" in idea_lower:
            risk_level = "high"
        elif complexity == Complexity.COMPLEX:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return ProjectAnalysis(
            project_type=project_type,
            complexity=complexity,
            needs_auth=needs_auth,
            needs_database=needs_database,
            needs_tests=needs_tests,
            needs_deployment=needs_deployment,
            risk_level=risk_level
        )
    
    def select_agents(self, analysis: ProjectAnalysis) -> List[str]:
        """
        Select which agents should run based on analysis and mode.
        """
        agents = []
        
        # Core agent - always runs
        agents.append("planner")
        
        # Mode overrides
        if self.mode == "simple":
            # Minimal: just planner + coder
            agents.append("coder")
            return agents
        
        # DB Schema agent
        if analysis.needs_database:
            agents.append("db_schema")
        
        # Auth agent
        if analysis.needs_auth:
            agents.append("auth")
        
        # Coder - always needed
        agents.append("coder")
        
        # Tests
        if analysis.needs_tests and self.mode != "simple":
            agents.append("tester")
        
        # Deployment
        if analysis.needs_deployment and self.mode == "production":
            agents.append("deployer")
        
        return agents
    
    def create_execution_order(self, selected_agents: List[str]) -> List[str]:
        """
        Create execution order respecting dependencies.
        Uses topological sort (Kahn's algorithm with deque for O(1) pops).
        """
        from collections import deque

        # Build dependency graph
        graph = {agent: [] for agent in selected_agents}
        in_degree = {agent: 0 for agent in selected_agents}
        
        for agent in selected_agents:
            deps = self.AGENT_DEPENDENCIES.get(agent, [])
            for dep in deps:
                if dep in selected_agents:
                    graph[dep].append(agent)
                    in_degree[agent] += 1
        
        # Topological sort (Kahn's algorithm)
        queue = deque(sorted(a for a in selected_agents if in_degree[a] == 0))
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in sorted(graph[current]):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Verify all agents included
        if len(result) != len(selected_agents):
            raise ValueError("Circular dependency detected in agent graph")
        
        return result
    
    def create_config(self, analysis: ProjectAnalysis) -> ExecutionConfig:
        """Create execution configuration based on analysis and mode"""
        if self.mode == "simple":
            return ExecutionConfig(
                skip_tests=True,
                strict_mode=False,
                depth="minimal"
            )
        elif self.mode == "production":
            return ExecutionConfig(
                skip_tests=False,
                strict_mode=True,
                depth="full"
            )
        else:  # full mode
            return ExecutionConfig(
                skip_tests=not analysis.needs_tests,
                strict_mode=True,
                depth="standard"
            )


# ========== PUBLIC API ==========

def create_execution_plan(
    user_idea: str,
    mode: Literal["simple", "full", "production"] = "full"
) -> ExecutionPlan:
    """
    Public API to create an execution plan.
    
    Args:
        user_idea: User's project description
        mode: Execution mode (simple/full/production)
        
    Returns:
        ExecutionPlan: JSON execution plan
    """
    brain = TeamLeadBrain(mode=mode)
    return brain.decide(user_idea)


# ========== EXAMPLE USAGE (FOR TESTING) ==========

if __name__ == "__main__":
    # Test simple project
    plan = create_execution_plan("build a todo app", mode="simple")
    print("SIMPLE MODE:")
    print(plan.model_dump_json(indent=2))
    print()
    
    # Test SaaS project
    plan = create_execution_plan(
        "build a SaaS app with authentication and payments",
        mode="production"
    )
    print("PRODUCTION MODE (SaaS):")
    print(plan.model_dump_json(indent=2))
    print()
    
    # Test medium complexity
    plan = create_execution_plan("build a blog with user auth and comments")
    print("FULL MODE (Medium complexity):")
    print(plan.model_dump_json(indent=2))
