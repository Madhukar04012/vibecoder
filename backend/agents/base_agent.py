"""
Base Agent — Phase-1

Base class for all strict-role agents.
Forces all LLM calls through the gateway for cost tracking.

Usage:
    class MyAgent(BaseAgent):
        name = "my_agent"
        
        def do_something(self, prompt):
            return self.call_llm([
                {"role": "system", "content": "You are an agent."},
                {"role": "user", "content": prompt}
            ])
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseAgent(ABC):
    """
    Base class for all Phase-1 strict-role agents.
    
    All agents MUST:
    1. Define a unique `name` attribute
    2. Use `self.call_llm()` for ALL LLM calls (never call LLM directly)
    3. Implement their specific methods
    """
    
    name: str = "base"  # Override in subclass
    
    def __init__(self):
        """Initialize the agent."""
        if self.name == "base":
            raise ValueError(
                f"Agent {self.__class__.__name__} must define a unique 'name' attribute"
            )
    
    def call_llm(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.3
    ) -> Optional[str]:
        """
        Make an LLM call through the gateway.
        
        This method MUST be used for all LLM calls.
        It automatically tracks tokens and costs for this agent.
        
        Args:
            messages: List of message dicts with "role" and "content"
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Response content as string, or None if call failed
        """
        from backend.engine.llm_gateway import llm_call
        return llm_call(
            agent_name=self.name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def call_llm_simple(
        self,
        system: str,
        user: str,
        max_tokens: int = 2048,
        temperature: float = 0.3
    ) -> Optional[str]:
        """
        Simplified LLM call with system/user strings.
        
        Args:
            system: System message content
            user: User message content
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            
        Returns:
            Response content or None
        """
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return self.call_llm(messages, max_tokens, temperature)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
