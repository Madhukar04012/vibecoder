"""
Product Manager Agent — Phase-1

Strict-role agent for creating Product Requirements Documents.
Runs ONLY in PLANNING state.

Usage:
    pm = ProductManagerAgent()
    prd = pm.generate_prd("Build a todo app with authentication")
"""

from typing import Dict, Any

from backend.agents.base_agent import BaseAgent
from backend.engine.llm_gateway import extract_json


SYSTEM_PROMPT = """You are a Senior Product Manager at a top tech company.
Your job is to create comprehensive Product Requirements Documents (PRDs).

Output ONLY valid JSON with this structure:
{
    "title": "Product title",
    "problem": "The core problem this solves",
    "scope": "What is in scope and out of scope",
    "description": "What this product does",
    "user_stories": ["As a user, I want...", ...],
    "user_flow": ["Step 1: User opens app", "Step 2: User sees...", ...],
    "features": ["Feature 1", "Feature 2", ...],
    "acceptance_criteria": ["Feature works when...", ...],
    "constraints": ["Must be responsive", "Max 3s load time", ...],
    "tech_hints": ["Use React", "REST API", ...]
}

RULES:
- Be comprehensive but realistic
- Include at least 5 user stories
- Include at least 5 features
- Include clear acceptance criteria
- No markdown, no explanation, JSON only
"""


class ProductManagerAgent(BaseAgent):
    """
    Product Manager agent for generating PRDs.
    
    State requirement: PLANNING
    Output: PRD as dict
    """
    
    name = "product_manager"
    
    def generate_prd(self, user_prompt: str) -> Dict[str, Any]:
        """
        Generate a Product Requirements Document.
        
        Args:
            user_prompt: User's project description
            
        Returns:
            PRD as dict with title, features, user_stories, etc.
        """
        response = self.call_llm_simple(
            system=SYSTEM_PROMPT,
            user=f"Create a comprehensive PRD for: {user_prompt}",
            max_tokens=2048,
            temperature=0.4
        )
        
        if not response:
            return self._fallback_prd(user_prompt)
        
        prd = extract_json(response)
        
        if not prd or not isinstance(prd, dict):
            return self._fallback_prd(user_prompt)
        
        # Ensure required fields exist
        return self._ensure_required_fields(prd, user_prompt)
    
    def _fallback_prd(self, user_prompt: str) -> Dict[str, Any]:
        """Create a minimal fallback PRD when LLM fails."""
        return {
            "title": user_prompt[:50],
            "problem": f"Users need a solution for: {user_prompt}",
            "scope": "Core functionality as described",
            "description": user_prompt,
            "user_stories": [
                f"As a user, I want to {user_prompt.lower()}",
                "As a user, I want a clean and intuitive interface",
                "As a user, I want fast and reliable performance",
            ],
            "user_flow": [
                "Step 1: User opens the application",
                "Step 2: User interacts with main feature",
                "Step 3: User completes their goal",
            ],
            "features": [
                "Core functionality",
                "Clean UI",
                "Responsive design",
                "Error handling",
            ],
            "acceptance_criteria": [
                "Application loads successfully",
                "Core features work as expected",
                "UI is responsive on mobile and desktop",
            ],
            "constraints": [
                "Must work in modern browsers",
                "Must be performant",
            ],
            "tech_hints": ["React", "Vite"],
        }
    
    def _ensure_required_fields(self, prd: dict, user_prompt: str) -> dict:
        """Ensure all required fields are present."""
        defaults = self._fallback_prd(user_prompt)
        
        for key in defaults:
            if key not in prd or not prd[key]:
                prd[key] = defaults[key]
        
        return prd
