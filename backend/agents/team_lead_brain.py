"""
Team Lead Brain - VibeCober's Decision Engine

This is the BRAIN that decides:
- Which agents should run
- In what order
- With what configuration

Does NOT execute agents. Only outputs JSON execution plans.
"""

from typing import List, Dict, Literal
import os
import re
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
    routing_source: Literal["keyword", "llm"] = "keyword"


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
        "code_reviewer",
        "tester",
        "deployer"
    }
    
    # Agent dependencies (what must run before what)
    AGENT_DEPENDENCIES = {
        "planner": [],
        "db_schema": ["planner"],
        "auth": ["db_schema"],  # Auth needs db_schema (user table)
        "coder": ["planner"],
        "code_reviewer": ["coder"],  # Review code after generation
        "tester": ["coder"],
        "deployer": ["tester"]
    }
    
    def __init__(self, mode: Literal["simple", "full", "production"] = "full"):
        self.mode = mode
        self._allow_llm_routing = os.getenv("TEAM_LEAD_LLM_ROUTING", "true").lower() == "true"
    
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
        matches = {
            ProjectType.SAAS: self._has_any(idea_lower, ["saas", "subscription", "payment", "billing"]),
            ProjectType.API: self._has_any(idea_lower, ["api", "rest", "graphql", "endpoint", "webhook"]),
            ProjectType.DASHBOARD: self._has_any(idea_lower, ["dashboard", "admin", "analytics", "metrics"]),
            ProjectType.AI_APP: self._has_any(idea_lower, ["ai", "ml", "llm", "chatbot", "agent"]),
            ProjectType.LANDING_PAGE: self._has_any(idea_lower, ["landing", "marketing", "website"]),
        }
        matched_types = [ptype for ptype, hit in matches.items() if hit]

        routing_source: Literal["keyword", "llm"] = "keyword"
        if len(matched_types) == 1:
            project_type = matched_types[0]
        elif self._is_ambiguous(idea_lower, matched_types):
            project_type = self._classify_with_llm(idea) or (matched_types[0] if matched_types else ProjectType.CRUD)
            if project_type in (ProjectType.SAAS, ProjectType.API, ProjectType.DASHBOARD, ProjectType.AI_APP, ProjectType.LANDING_PAGE, ProjectType.CRUD):
                routing_source = "llm" if project_type != (matched_types[0] if matched_types else ProjectType.CRUD) or not matched_types else "keyword"
        else:
            project_type = matched_types[0] if matched_types else ProjectType.CRUD
        
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
            risk_level=risk_level,
            routing_source=routing_source,
        )

    @staticmethod
    def _has_any(text: str, terms: List[str]) -> bool:
        return any(term in text for term in terms)

    def _is_ambiguous(self, idea_lower: str, matched_types: List[ProjectType]) -> bool:
        if len(matched_types) == 0:
            return len(idea_lower.split()) > 3
        if len(matched_types) > 1:
            return True
        # Single weak match with uncertain intent
        weak_terms = {"website", "app", "platform", "tool", "system"}
        tokens = set(re.findall(r"[a-zA-Z]+", idea_lower))
        return bool(tokens & weak_terms) and len(tokens) <= 8


    def _classify_with_llm(self, idea: str) -> ProjectType | None:
        """Fallback classifier for ambiguous routing."""
        if not self._allow_llm_routing:
            return None

        has_remote_key = bool(os.getenv("NIM_API_KEY", "").strip())
        if not has_remote_key:
            return None

        try:
            from backend.engine.llm_gateway import llm_call_simple
        except Exception:
            return None

        response = llm_call_simple(
            agent_name="team_lead_brain",
            system=(
                "Classify product intent into exactly one label: "
                "saas, crud, api, dashboard, ai_app, landing_page. "
                "Reply with label only."
            ),
            user=f"Idea: {idea}",
            max_tokens=16,
            temperature=0.0,
        )
        if not response:
            return None

        label = response.strip().lower().replace("-", "_")
        aliases = {
            "saas": ProjectType.SAAS,
            "crud": ProjectType.CRUD,
            "api": ProjectType.API,
            "dashboard": ProjectType.DASHBOARD,
            "ai_app": ProjectType.AI_APP,
            "ai": ProjectType.AI_APP,
            "landing_page": ProjectType.LANDING_PAGE,
            "landing": ProjectType.LANDING_PAGE,
            "website": ProjectType.LANDING_PAGE,
        }
        return aliases.get(label)
    
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
        
        # Code reviewer - quality gate for full and production modes
        if self.mode in ("full", "production"):
            agents.append("code_reviewer")
        
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
