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
from backend.core.tech_detector import detect_stack


SYSTEM_PROMPT = """You are a Principal Product Manager at a FAANG company.
Your job is to create comprehensive, S-class Product Requirements Documents (PRDs)
that result in production-quality software.

IMPORTANT: The tech_hints field should reflect EXACTLY what technologies
the user mentioned in their prompt. Do NOT default to React if they asked
for Vue, Angular, Django, Go, etc. If no tech is specified, recommend the
best modern stack for the project type.

Output ONLY valid JSON with this structure:
{
    "title": "Product title — professional and descriptive",
    "problem": "Clear problem statement with target users and pain points",
    "scope": "In-scope and out-of-scope items, clearly separated",
    "description": "Detailed product description covering core value proposition",
    "target_audience": "Primary and secondary user personas",
    "user_stories": [
        "As a [user type], I want [action] so that [benefit]",
        ... (at least 8 stories covering all core features)
    ],
    "user_flow": [
        "Step 1: User lands on the app → sees hero section with CTA",
        "Step 2: User clicks Sign Up → modal/page with form validation",
        ... (detailed step-by-step flow covering the full user journey)
    ],
    "features": {
        "core": ["Feature 1 — detailed description", ...],
        "auth": ["JWT login/register", "Protected routes", "Role-based access"],
        "ui": ["Responsive design with mobile-first approach", "Dark/light theme", "Loading states", "Error boundaries", "Toast notifications"],
        "data": ["CRUD operations", "Pagination", "Search/filter", "Real-time updates"],
        "devops": ["Docker containerization", "CI/CD pipeline", "Environment configuration", "Structured logging"]
    },
    "pages": [
        {"name": "Home", "route": "/", "components": ["Hero", "Features", "CTA"], "description": "Landing page"},
        {"name": "Dashboard", "route": "/dashboard", "components": ["Stats", "RecentActivity", "QuickActions"], "description": "Main user dashboard"},
        ... (ALL pages the app needs with their components and routes)
    ],
    "components": [
        {"name": "Header", "type": "layout", "description": "Navigation bar with auth-aware menu"},
        {"name": "Footer", "type": "layout", "description": "Footer with links and social"},
        {"name": "Button", "type": "ui", "description": "Reusable button with variants"},
        ... (ALL components with their type: layout/ui/feature/page)
    ],
    "api_endpoints": [
        {"method": "POST", "path": "/api/v1/auth/login", "description": "User login", "request": "email, password", "response": "token, user"},
        {"method": "POST", "path": "/api/v1/auth/register", "description": "User registration", "request": "name, email, password", "response": "token, user"},
        ... (ALL API endpoints with request/response shapes)
    ],
    "data_models": [
        {"name": "User", "fields": ["id", "email", "name", "password_hash", "role", "created_at"]},
        ... (ALL database models with their fields)
    ],
    "acceptance_criteria": [
        "Authentication: Login, register, logout, token refresh all work correctly",
        "Responsive: All pages look good on mobile (375px), tablet (768px), and desktop (1440px)",
        "Performance: First Contentful Paint < 1.5s, no layout shifts",
        "Accessibility: All interactive elements have aria-labels, keyboard navigable",
        "Error handling: All API calls have error states, form validation shows inline errors",
        ... (detailed, testable criteria)
    ],
    "non_functional_requirements": [
        "Performance: Page load < 2s, API response < 500ms",
        "Security: OWASP Top 10 compliance, input sanitization, HTTPS",
        "Scalability: Stateless backend, database indexing on frequently queried fields",
        "Monitoring: Structured logs, health check endpoint"
    ],
    "constraints": [
        "Must be responsive across all device sizes",
        "Must support latest 2 versions of Chrome, Firefox, Safari, Edge",
        "Max bundle size: 200KB gzipped for initial load",
        "Must pass WCAG 2.1 AA accessibility standards"
    ],
    "tech_hints": ["<EXACT technologies from user prompt>"],
    "design_system": {
        "colors": "Professional palette with primary, secondary, accent, destructive",
        "typography": "Inter or system fonts, clear hierarchy (h1-h6, body, caption)",
        "spacing": "Consistent 4px/8px grid system via Tailwind",
        "components": "shadcn/ui-style composable components"
    }
}

RULES:
- Be EXTREMELY comprehensive — this PRD drives the entire project generation
- Include at least 8 user stories covering all features
- Include at least 6 pages with their components and routes
- Include at least 10 UI components (layout + ui + feature types)
- Include at least 8 API endpoints with request/response shapes
- Include at least 3 data models with all fields
- Pages must have component breakdown — this maps directly to file structure
- tech_hints MUST match the user's requested technologies exactly
- If user doesn't specify tech, recommend: React 19 + Vite + TypeScript + Tailwind for frontend, FastAPI + Pydantic + SQLAlchemy for backend
- ALWAYS include auth features unless explicitly excluded
- ALWAYS include responsive design requirements
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
        """Create an S-class fallback PRD when LLM fails, using detected tech."""
        detected = detect_stack(user_prompt)
        
        # Build tech hints from detected technologies
        tech_hints = []
        if detected.backend_framework:
            tech_hints.append(detected.backend_framework)
        if detected.frontend_framework:
            tech_hints.append(detected.frontend_framework)
        if detected.database:
            tech_hints.append(detected.database)
        if detected.styling:
            tech_hints.append(detected.styling)
        for lang in detected.languages:
            tech_hints.append(lang.capitalize())
        # If nothing detected, default to S-class stack
        if not tech_hints:
            tech_hints = ["React 19", "TypeScript", "Vite", "Tailwind CSS", "FastAPI", "Pydantic", "SQLAlchemy"]
        
        title = user_prompt[:80].strip()
        
        return {
            "title": title,
            "problem": f"Users need a modern, production-quality solution for: {user_prompt}",
            "scope": "Full-stack application with authentication, core features, and deployment configuration",
            "description": user_prompt,
            "target_audience": "End users who need a reliable, intuitive application",
            "user_stories": [
                f"As a user, I want to {user_prompt.lower()} so that I can accomplish my goal",
                "As a user, I want to sign up and log in securely so that my data is protected",
                "As a user, I want a clean and intuitive interface so that I can navigate easily",
                "As a user, I want fast page loads so that I don't waste time waiting",
                "As a user, I want the app to work on my phone so that I can use it anywhere",
                "As a user, I want proper error messages so that I know what went wrong",
                "As a user, I want to search and filter content so that I can find what I need",
                "As an admin, I want a dashboard so that I can manage content and users",
            ],
            "user_flow": [
                "Step 1: User lands on the home page → hero section with CTA",
                "Step 2: User clicks Sign Up → registration form with validation",
                "Step 3: User completes registration → redirected to dashboard",
                "Step 4: User explores main features from the sidebar/nav",
                "Step 5: User interacts with core feature → creates/views/edits content",
                "Step 6: User receives feedback via toast notifications",
            ],
            "features": {
                "core": [
                    f"Core functionality: {user_prompt[:60]}",
                    "Dashboard with overview stats and recent activity",
                    "Search and filter capabilities",
                    "CRUD operations for main entities",
                ],
                "auth": [
                    "JWT-based authentication with refresh tokens",
                    "Login and registration with form validation",
                    "Protected routes and role-based access control",
                    "Password reset flow",
                ],
                "ui": [
                    "Responsive design with mobile-first approach",
                    "Dark/light theme toggle",
                    "Loading skeletons and spinners",
                    "Error boundaries with fallback UI",
                    "Toast notifications for user feedback",
                    "Accessible components with keyboard navigation",
                ],
                "data": [
                    "Paginated data tables",
                    "Real-time form validation with Zod",
                    "API error handling with retry logic",
                ],
                "devops": [
                    "Docker containerization",
                    "CI/CD with GitHub Actions",
                    "Environment variable configuration",
                    "Structured logging",
                ],
            },
            "pages": [
                {"name": "Home", "route": "/", "components": ["Hero", "Features", "CTA"], "description": "Landing page"},
                {"name": "Login", "route": "/login", "components": ["LoginForm"], "description": "User login"},
                {"name": "Register", "route": "/register", "components": ["RegisterForm"], "description": "User registration"},
                {"name": "Dashboard", "route": "/dashboard", "components": ["Stats", "RecentActivity", "QuickActions"], "description": "Main dashboard"},
                {"name": "Settings", "route": "/settings", "components": ["ProfileForm", "PasswordForm", "ThemeToggle"], "description": "User settings"},
                {"name": "NotFound", "route": "*", "components": ["NotFoundContent"], "description": "404 page"},
            ],
            "components": [
                {"name": "Header", "type": "layout", "description": "Navigation with auth-aware menu"},
                {"name": "Footer", "type": "layout", "description": "Footer with links"},
                {"name": "Sidebar", "type": "layout", "description": "Navigation sidebar for dashboard"},
                {"name": "Button", "type": "ui", "description": "Button with variants and loading state"},
                {"name": "Input", "type": "ui", "description": "Input with label and error display"},
                {"name": "Card", "type": "ui", "description": "Card container"},
                {"name": "Dialog", "type": "ui", "description": "Modal dialog"},
                {"name": "LoadingSpinner", "type": "ui", "description": "Loading indicator"},
                {"name": "Toast", "type": "ui", "description": "Notification toast"},
                {"name": "ErrorBoundary", "type": "ui", "description": "Error boundary wrapper"},
            ],
            "api_endpoints": [
                {"method": "GET", "path": "/health", "description": "Health check"},
                {"method": "POST", "path": "/api/v1/auth/login", "description": "Login"},
                {"method": "POST", "path": "/api/v1/auth/register", "description": "Register"},
                {"method": "GET", "path": "/api/v1/auth/me", "description": "Get current user"},
                {"method": "GET", "path": "/api/v1/items", "description": "List items"},
                {"method": "POST", "path": "/api/v1/items", "description": "Create item"},
                {"method": "GET", "path": "/api/v1/items/{id}", "description": "Get item"},
                {"method": "PUT", "path": "/api/v1/items/{id}", "description": "Update item"},
                {"method": "DELETE", "path": "/api/v1/items/{id}", "description": "Delete item"},
            ],
            "data_models": [
                {"name": "User", "fields": ["id", "email", "name", "password_hash", "role", "created_at", "updated_at"]},
                {"name": "Item", "fields": ["id", "title", "description", "user_id", "status", "created_at", "updated_at"]},
            ],
            "acceptance_criteria": [
                "Auth: Login, register, and logout work correctly with proper validation",
                "Responsive: All pages render correctly on mobile, tablet, and desktop",
                "Performance: First Contentful Paint < 1.5s",
                "Error handling: All API calls show loading and error states",
                "Accessibility: All interactive elements have proper labels",
            ],
            "non_functional_requirements": [
                "Performance: Page load < 2s, API response < 500ms",
                "Security: Input sanitization, parameterized queries, JWT auth",
                "Scalability: Stateless backend, proper database indexing",
            ],
            "constraints": [
                "Must be responsive across all device sizes",
                "Must support latest browsers",
            ],
            "tech_hints": tech_hints,
            "design_system": {
                "colors": "Professional palette with primary, secondary, accent",
                "typography": "Inter/system fonts with clear hierarchy",
                "spacing": "Consistent 4px/8px grid via Tailwind",
                "components": "shadcn/ui-style composable components",
            },
        }
    
    def _ensure_required_fields(self, prd: dict, user_prompt: str) -> dict:
        """Ensure all required fields are present."""
        defaults = self._fallback_prd(user_prompt)
        
        for key in defaults:
            if key not in prd or not prd[key]:
                prd[key] = defaults[key]
        
        return prd
