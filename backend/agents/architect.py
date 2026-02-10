"""
Architect Agent — Phase-1

Strict-role agent for creating system architecture and file plans.
Runs ONLY in PLANNING state.

Usage:
    architect = ArchitectAgent()
    roadmap = architect.generate_roadmap(prd)
"""

from typing import Dict, Any, List

from backend.agents.base_agent import BaseAgent
from backend.engine.llm_gateway import extract_json


SYSTEM_PROMPT = """You are a Senior Software Architect at a top tech company.
Based on the PRD, design a COMPANY-LEVEL production system.

Output ONLY valid JSON with this structure:
{
    "architecture": "Brief description of the architecture",
    "stack": {
        "frontend": "React + Vite",
        "styling": "CSS Modules",
        "state": "React Hooks"
    },
    "modules": [
        {"name": "Core", "description": "Main application logic"},
        {"name": "UI", "description": "User interface components"}
    ],
    "directory_structure": [
        "package.json",
        "vite.config.js",
        "index.html",
        "src/main.jsx",
        "src/App.jsx",
        "src/App.css",
        "src/components/Header.jsx",
        "src/components/Header.css",
        "src/pages/Home.jsx",
        "src/hooks/useLocalStorage.js",
        "src/utils/helpers.js"
    ],
    "component_tree": {
        "App": ["Layout"],
        "Layout": ["Header", "MainContent", "Footer"]
    },
    "data_flow": "User actions → Components → State → API → Database",
    "api_endpoints": [
        {"method": "GET", "path": "/api/items", "description": "List items"}
    ],
    "risks": [
        "Performance with large datasets",
        "Browser compatibility"
    ],
    "milestones": [
        {"phase": 1, "name": "Core Setup", "files": ["package.json", "vite.config.js"]},
        {"phase": 2, "name": "Main Features", "files": ["src/App.jsx", "src/components/*"]}
    ]
}

RULES:
- Include AT LEAST 10-15 files for a proper project
- Include components/, pages/, hooks/, utils/ directories
- Include CSS files for styling
- package.json MUST include react, react-dom, vite
- Be comprehensive but realistic
- No markdown, no explanation, JSON only
"""


class ArchitectAgent(BaseAgent):
    """
    Architect agent for generating system architecture and file plans.
    
    State requirement: PLANNING
    Output: Roadmap as dict with architecture, modules, directory_structure
    """
    
    name = "architect"
    
    def generate_roadmap(self, prd: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a system architecture and implementation roadmap.
        
        Args:
            prd: Product Requirements Document from PM
            
        Returns:
            Roadmap dict with architecture, modules, directory_structure, etc.
        """
        import json
        
        prd_text = json.dumps(prd, indent=2) if isinstance(prd, dict) else str(prd)
        
        response = self.call_llm_simple(
            system=SYSTEM_PROMPT,
            user=f"Design the system architecture based on this PRD:\n\n{prd_text}",
            max_tokens=2048,
            temperature=0.3
        )
        
        if not response:
            return self._fallback_roadmap(prd)
        
        roadmap = extract_json(response)
        
        if not roadmap or not isinstance(roadmap, dict):
            return self._fallback_roadmap(prd)
        
        # Ensure required fields
        return self._ensure_required_fields(roadmap, prd)
    
    def _fallback_roadmap(self, prd: Dict[str, Any]) -> Dict[str, Any]:
        """Create a minimal fallback roadmap when LLM fails."""
        return {
            "architecture": "Single-page React application with component-based architecture",
            "stack": {
                "frontend": "React + Vite",
                "styling": "CSS",
                "state": "React Hooks"
            },
            "modules": [
                {"name": "Core", "description": "Application entry and routing"},
                {"name": "Components", "description": "Reusable UI components"},
                {"name": "Pages", "description": "Page-level components"},
                {"name": "Utils", "description": "Helper functions"},
            ],
            "directory_structure": [
                "package.json",
                "vite.config.js",
                "index.html",
                "src/main.jsx",
                "src/App.jsx",
                "src/App.css",
                "src/index.css",
                "src/components/Header.jsx",
                "src/components/Footer.jsx",
                "src/pages/Home.jsx",
                "src/utils/helpers.js",
            ],
            "component_tree": {
                "App": ["Header", "MainContent", "Footer"]
            },
            "data_flow": "User Input → Components → State → Render",
            "api_endpoints": [],
            "risks": [
                "Performance optimization may be needed",
                "Cross-browser testing required"
            ],
            "milestones": [
                {"phase": 1, "name": "Setup", "files": ["package.json", "vite.config.js", "index.html"]},
                {"phase": 2, "name": "Core App", "files": ["src/main.jsx", "src/App.jsx"]},
                {"phase": 3, "name": "Components", "files": ["src/components/*"]},
            ]
        }
    
    def _ensure_required_fields(self, roadmap: dict, prd: Dict[str, Any]) -> dict:
        """Ensure all required fields are present."""
        defaults = self._fallback_roadmap(prd)
        
        for key in defaults:
            if key not in roadmap or not roadmap[key]:
                roadmap[key] = defaults[key]
        
        # Ensure directory_structure is a list
        if not isinstance(roadmap.get("directory_structure"), list):
            roadmap["directory_structure"] = defaults["directory_structure"]
        
        return roadmap
    
    def get_file_plan(self, roadmap: Dict[str, Any]) -> List[str]:
        """
        Extract the file plan from a roadmap.
        
        Args:
            roadmap: Roadmap dict
            
        Returns:
            List of file paths to create
        """
        return roadmap.get("directory_structure", [])
