"""
Agent Registry - Central catalog of all VibeCober agents

Defines available agents, their execution functions, and dependencies.
Used by Team Lead Brain and Orchestrator.
"""

from typing import Dict, Any, Callable
from dataclasses import dataclass
from functools import lru_cache
import importlib


@dataclass
class AgentSpec:
    """Specification for an agent"""
    name: str
    module: str
    function: str
    dependencies: list[str]
    description: str


class AgentRegistry:
    """Central registry of all agents"""
    
    def __init__(self):
        self._agents: Dict[str, AgentSpec] = {}
        self._register_default_agents()
    
    def _register_default_agents(self):
        """Register all default agents"""
        
        self.register(AgentSpec(
            name="planner",
            module="backend.agents.planner",
            function="planner_agent",
            dependencies=[],
            description="Decides project architecture and tech stack"
        ))
        
        self.register(AgentSpec(
            name="db_schema",
            module="backend.agents.db_schema",
            function="db_schema_agent",
            dependencies=["planner"],
            description="Generates database schema and models"
        ))
        
        self.register(AgentSpec(
            name="auth",
            module="backend.agents.auth_agent",
            function="auth_agent",
            dependencies=["db_schema"],
            description="Generates authentication system"
        ))
        
        self.register(AgentSpec(
            name="coder",
            module="backend.agents.coder",
            function="code_agent",
            dependencies=["planner"],
            description="Generates project code structure"
        ))
        
        self.register(AgentSpec(
            name="tester",
            module="backend.agents.test_agent",
            function="run_test_agent",
            dependencies=["coder"],
            description="Generates tests for the project"
        ))
        
        self.register(AgentSpec(
            name="deployer",
            module="backend.agents.deploy_agent",
            function="deploy_agent",
            dependencies=["tester"],
            description="Generates deployment configuration"
        ))
        
        self.register(AgentSpec(
            name="code_reviewer",
            module="backend.agents.code_reviewer",
            function="review_code",
            dependencies=["coder"],
            description="Reviews generated code for S-class quality standards"
        ))
    
    def register(self, spec: AgentSpec):
        """Register a new agent"""
        self._agents[spec.name] = spec
    
    def get(self, name: str) -> AgentSpec:
        """Get agent spec by name"""
        if name not in self._agents:
            raise ValueError(f"Agent '{name}' not found in registry")
        return self._agents[name]
    
    def get_function(self, name: str) -> Callable:
        """Get agent's execution function (cached after first import)"""
        spec = self.get(name)
        return _import_agent_function(spec.module, spec.function)
    
    def list_all(self) -> list[str]:
        """List all registered agent names"""
        return list(self._agents.keys())
    
    def get_dependencies(self, name: str) -> list[str]:
        """Get dependencies for an agent"""
        return self.get(name).dependencies


# Global registry instance
_registry = AgentRegistry()


@lru_cache(maxsize=None)
def _import_agent_function(module_path: str, func_name: str) -> Callable:
    """Import and cache an agent function to avoid repeated dynamic imports."""
    module = importlib.import_module(module_path)
    if not hasattr(module, func_name):
        raise AttributeError(f"Function '{func_name}' not found in module '{module_path}'")
    return getattr(module, func_name)


# ========== PUBLIC API ==========

def get_registry() -> AgentRegistry:
    """Get the global agent registry"""
    return _registry


def get_agent_function(name: str) -> Callable:
    """Get agent function by name"""
    return _registry.get_function(name)


def list_agents() -> list[str]:
    """List all available agents"""
    return _registry.list_all()
