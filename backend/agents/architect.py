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
from backend.core.tech_detector import detect_stack, get_architect_prompt_for_stack, get_fallback_architecture


SYSTEM_PROMPT = """You are a Principal Software Architect at a FAANG-level company.
You are designing the architecture for a PRODUCTION system that a real engineering team would ship.

CRITICAL — Analyze the PRD carefully to determine the CORRECT technology stack:
- If the user asks for Python/Django/Flask/FastAPI → generate Python files (.py)
- If the user asks for Node/Express/NestJS → generate JS/TS files
- If the user asks for Go/Gin → generate Go files (.go)
- If the user asks for Java/Spring → generate Java files (.java)
- If the user asks for Vue/Angular/Svelte → use those frameworks, NOT React
- If no specific tech is mentioned, choose the BEST tech for the described project

S-CLASS ARCHITECTURE STANDARDS (non-negotiable):
1. MINIMUM 25-40 files for a proper project — real projects have many files
2. Frontend MUST use TypeScript (.tsx/.ts) not JavaScript (.jsx/.js)
3. Frontend MUST have: components/ui/, components/layout/, pages/, hooks/, lib/, stores/, types/
4. Backend MUST have: api/v1/, core/, models/, schemas/, services/, middleware/, utils/, tests/
5. Include config files: tsconfig.json, tailwind.config.ts, eslint.config.js, .prettierrc, docker-compose.yml
6. Include DevOps: Dockerfile, .github/workflows/ci.yml, .dockerignore, Makefile
7. Include proper testing: vitest.config.ts (frontend), conftest.py + test files (backend)
8. Include security: proper auth, env-based config, no hardcoded secrets
9. Include documentation: README.md with setup guide, architecture overview
10. Frontend components: button, input, card, dialog, loading-spinner, toast (shadcn/ui style)

Output ONLY valid JSON with this structure:
{
    "architecture": "Detailed description of the architecture pattern (e.g., Clean Architecture with service layer)",
    "stack": {
        "backend": "<framework>",
        "frontend": "<framework>",
        "database": "<database>",
        "styling": "Tailwind CSS",
        "state_management": "<e.g., Zustand, TanStack Query>",
        "auth": "JWT + bcrypt",
        "deployment": "Docker"
    },
    "modules": [
        {"name": "Module Name", "description": "What it does", "files": ["file1.ts", "file2.ts"]}
    ],
    "directory_structure": [
        "README.md",
        ".gitignore",
        "docker-compose.yml",
        "Makefile",
        ".github/workflows/ci.yml",
        "backend/main.py",
        "backend/requirements.txt",
        "backend/Dockerfile",
        "backend/.env.example",
        "backend/app/core/config.py",
        "backend/app/core/security.py",
        "backend/app/core/database.py",
        "backend/app/core/exceptions.py",
        "backend/app/api/v1/router.py",
        "backend/app/api/deps.py",
        "backend/app/models/__init__.py",
        "backend/app/schemas/common.py",
        "backend/app/services/__init__.py",
        "backend/app/middleware/error_handler.py",
        "backend/tests/conftest.py",
        "backend/tests/test_health.py",
        "frontend/package.json",
        "frontend/tsconfig.json",
        "frontend/vite.config.ts",
        "frontend/tailwind.config.ts",
        "frontend/eslint.config.js",
        "frontend/index.html",
        "frontend/src/main.tsx",
        "frontend/src/App.tsx",
        "frontend/src/index.css",
        "frontend/src/components/ui/button.tsx",
        "frontend/src/components/ui/input.tsx",
        "frontend/src/components/ui/card.tsx",
        "frontend/src/components/layout/header.tsx",
        "frontend/src/components/layout/footer.tsx",
        "frontend/src/lib/api-client.ts",
        "frontend/src/lib/utils.ts",
        "frontend/src/hooks/use-auth.ts",
        "frontend/src/stores/auth-store.ts",
        "frontend/src/types/index.ts",
        "frontend/src/pages/home.tsx",
        "... include ALL feature-specific files"
    ],
    "component_tree": {
        "App": ["RootLayout > [Header, main > Routes, Footer]"]
    },
    "data_flow": "Client → API Client (with auth interceptors) → FastAPI Router → Service Layer → Repository → Database",
    "api_endpoints": [
        {"method": "GET", "path": "/health", "description": "Health check"},
        {"method": "POST", "path": "/api/v1/auth/login", "description": "User login"},
        {"method": "POST", "path": "/api/v1/auth/register", "description": "User registration"},
        {"method": "GET", "path": "/api/v1/auth/me", "description": "Current user profile"}
    ],
    "risks": ["Risk 1", "Risk 2"],
    "milestones": [
        {"phase": 1, "name": "Foundation", "files": ["config files", "core setup"]},
        {"phase": 2, "name": "Core Features", "files": ["main feature files"]},
        {"phase": 3, "name": "Polish & Deploy", "files": ["tests", "CI/CD", "docs"]}
    ]
}

RULES:
- Include AT LEAST 25-40 files for a proper S-class project
- Use CORRECT file extensions for the chosen technology
- TypeScript for frontend — ALWAYS .tsx/.ts, never .jsx/.js
- Include proper directory hierarchy with at least 3 levels of nesting
- Every module must map to actual files in directory_structure
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
        
        # Detect stack from PRD description/title for better prompting
        user_desc = prd.get("description", prd.get("title", "")) if isinstance(prd, dict) else str(prd)
        detected = detect_stack(user_desc)
        
        # Use stack-aware system prompt if technologies were detected
        if detected.backend_framework or detected.frontend_framework or detected.languages:
            system = get_architect_prompt_for_stack(detected)
        else:
            system = SYSTEM_PROMPT
        
        response = self.call_llm_simple(
            system=system,
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
        """Create a fallback roadmap when LLM fails, based on detected tech — S-class quality."""
        user_desc = prd.get("description", prd.get("title", "")) if isinstance(prd, dict) else str(prd)
        detected = detect_stack(user_desc)
        
        fallback_arch = get_fallback_architecture(detected, user_desc)
        
        # Use S-class file plan for comprehensive structure
        from backend.standards.quality_standards import get_sclass_file_plan
        
        features = prd.get("features", []) if isinstance(prd, dict) else []
        stack = fallback_arch.get("stack", {})
        
        sclass_files = get_sclass_file_plan(
            project_type=prd.get("title", "web app") if isinstance(prd, dict) else "web app",
            features=features,
            tech_stack=stack,
        )
        
        # Merge with fallback architecture files
        all_files = list(set(
            sclass_files + fallback_arch.get("directory_structure", [])
        ))
        all_files.sort()
        
        return {
            "architecture": f"Clean Architecture with {stack.get('backend', 'FastAPI')} + {stack.get('frontend', 'React')} + Service Layer Pattern",
            "stack": {
                **stack,
                "styling": stack.get("styling", "Tailwind CSS"),
                "state_management": "Zustand + TanStack Query",
                "auth": "JWT + bcrypt",
                "deployment": "Docker",
            },
            "modules": [
                {"name": "Core", "description": "Application entry, config, and routing", "files": []},
                {"name": "Auth", "description": "Authentication and authorization", "files": []},
                {"name": "API", "description": "API routes, schemas, and validation", "files": []},
                {"name": "Data", "description": "Database models and migrations", "files": []},
                {"name": "Services", "description": "Business logic layer", "files": []},
                {"name": "UI", "description": "Frontend components and pages", "files": []},
                {"name": "DevOps", "description": "Docker, CI/CD, deployment", "files": []},
            ],
            "directory_structure": all_files,
            "component_tree": {"App": ["RootLayout > [Header, Routes, Footer]"]},
            "data_flow": "Client → API Client → Router → Service → Repository → Database",
            "api_endpoints": [
                {"method": "GET", "path": "/health", "description": "Health check"},
                {"method": "POST", "path": "/api/v1/auth/login", "description": "Login"},
                {"method": "POST", "path": "/api/v1/auth/register", "description": "Register"},
            ],
            "risks": [
                "Performance optimization may be needed under load",
                "Security review recommended before production",
            ],
            "milestones": [
                {"phase": 1, "name": "Foundation", "files": all_files[:8]},
                {"phase": 2, "name": "Core Features", "files": all_files[8:20]},
                {"phase": 3, "name": "Polish & Deploy", "files": all_files[20:]},
            ],
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
