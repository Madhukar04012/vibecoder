"""
Tech Stack Detector — Analyzes user prompts to detect requested technologies.

This module extracts languages, frameworks, databases, styling, and other tech
from a user's project description so the pipeline can generate appropriate code.

Usage:
    from backend.core.tech_detector import detect_stack, TechStack

    stack = detect_stack("Build a Django REST API with PostgreSQL and Vue.js frontend")
    print(stack.backend_framework)  # "Django"
    print(stack.frontend_framework)  # "Vue"
    print(stack.languages)  # ["python", "javascript"]
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ── Keyword → technology mappings ────────────────────────────────────────────

BACKEND_FRAMEWORKS: Dict[str, Tuple[str, str]] = {
    # keyword → (framework_name, language)
    "fastapi": ("FastAPI", "python"),
    "fast api": ("FastAPI", "python"),
    "flask": ("Flask", "python"),
    "django": ("Django", "python"),
    "express": ("Express", "javascript"),
    "express.js": ("Express", "javascript"),
    "expressjs": ("Express", "javascript"),
    "nestjs": ("NestJS", "typescript"),
    "nest.js": ("NestJS", "typescript"),
    "koa": ("Koa", "javascript"),
    "hapi": ("Hapi", "javascript"),
    "spring boot": ("Spring Boot", "java"),
    "spring": ("Spring Boot", "java"),
    "gin": ("Gin", "go"),
    "fiber": ("Fiber", "go"),
    "echo": ("Echo", "go"),
    "actix": ("Actix", "rust"),
    "rocket": ("Rocket", "rust"),
    "axum": ("Axum", "rust"),
    "laravel": ("Laravel", "php"),
    "symfony": ("Symfony", "php"),
    "rails": ("Rails", "ruby"),
    "ruby on rails": ("Rails", "ruby"),
    "asp.net": ("ASP.NET", "csharp"),
    ".net": ("ASP.NET", "csharp"),
    "dotnet": ("ASP.NET", "csharp"),
}

FRONTEND_FRAMEWORKS: Dict[str, Tuple[str, str]] = {
    # keyword → (framework_name, language)
    "react": ("React", "javascript"),
    "reactjs": ("React", "javascript"),
    "react.js": ("React", "javascript"),
    "next.js": ("Next.js", "typescript"),
    "nextjs": ("Next.js", "typescript"),
    "next": ("Next.js", "typescript"),
    "vue": ("Vue", "javascript"),
    "vuejs": ("Vue", "javascript"),
    "vue.js": ("Vue", "javascript"),
    "nuxt": ("Nuxt", "javascript"),
    "nuxt.js": ("Nuxt", "javascript"),
    "nuxtjs": ("Nuxt", "javascript"),
    "angular": ("Angular", "typescript"),
    "svelte": ("Svelte", "javascript"),
    "sveltekit": ("SvelteKit", "javascript"),
    "solid": ("SolidJS", "javascript"),
    "solidjs": ("SolidJS", "javascript"),
    "astro": ("Astro", "javascript"),
    "remix": ("Remix", "typescript"),
    "gatsby": ("Gatsby", "javascript"),
    "htmx": ("HTMX", "javascript"),
    "jquery": ("jQuery", "javascript"),
    "flutter": ("Flutter", "dart"),
    "react native": ("React Native", "javascript"),
    "electron": ("Electron", "javascript"),
    "tauri": ("Tauri", "rust"),
    "tkinter": ("Tkinter", "python"),
    "streamlit": ("Streamlit", "python"),
    "gradio": ("Gradio", "python"),
}

DATABASES: Dict[str, str] = {
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mariadb": "MariaDB",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "sqlite": "SQLite",
    "redis": "Redis",
    "firebase": "Firebase",
    "firestore": "Firestore",
    "supabase": "Supabase",
    "dynamodb": "DynamoDB",
    "cassandra": "Cassandra",
    "neo4j": "Neo4j",
    "cockroachdb": "CockroachDB",
    "elasticsearch": "Elasticsearch",
}

STYLING: Dict[str, str] = {
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "bootstrap": "Bootstrap",
    "material ui": "Material UI",
    "material-ui": "Material UI",
    "mui": "Material UI",
    "chakra": "Chakra UI",
    "chakra ui": "Chakra UI",
    "ant design": "Ant Design",
    "antd": "Ant Design",
    "styled-components": "Styled Components",
    "styled components": "Styled Components",
    "scss": "SCSS",
    "sass": "SASS",
    "less": "LESS",
    "css modules": "CSS Modules",
    "shadcn": "shadcn/ui",
}

LANGUAGES: Dict[str, str] = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "java": "java",
    "kotlin": "kotlin",
    "go": "go",
    "golang": "go",
    "rust": "rust",
    "ruby": "ruby",
    "php": "php",
    "c#": "csharp",
    "csharp": "csharp",
    "c sharp": "csharp",
    "swift": "swift",
    "dart": "dart",
    "elixir": "elixir",
    "scala": "scala",
    "r lang": "r",
    "lua": "lua",
    "perl": "perl",
    "c++": "cpp",
    "cpp": "cpp",
    "c lang": "c",
}

EXTRAS: Dict[str, str] = {
    "docker": "Docker",
    "graphql": "GraphQL",
    "grpc": "gRPC",
    "websocket": "WebSocket",
    "socket.io": "Socket.IO",
    "oauth": "OAuth",
    "jwt": "JWT",
    "stripe": "Stripe",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "prisma": "Prisma",
    "drizzle": "Drizzle ORM",
    "sqlalchemy": "SQLAlchemy",
    "mongoose": "Mongoose",
    "typeorm": "TypeORM",
    "sequelize": "Sequelize",
}

# ── Project type patterns ────────────────────────────────────────────────────

PROJECT_TYPE_PATTERNS: Dict[str, List[str]] = {
    "cli": ["cli", "command line", "terminal app", "console app", "command-line"],
    "api": ["rest api", "api", "graphql", "grpc", "microservice", "backend only", "api server"],
    "fullstack": ["full stack", "fullstack", "full-stack"],
    "mobile": ["mobile app", "ios app", "android app", "flutter", "react native"],
    "desktop": ["desktop app", "electron", "tauri", "tkinter"],
    "game": ["game", "pygame", "unity", "godot"],
    "ml": ["machine learning", "ml model", "neural network", "deep learning", "ai model"],
    "data": ["data pipeline", "etl", "data processing", "scraper", "web scraping", "crawler"],
    "devops": ["ci/cd", "pipeline", "deployment", "infrastructure"],
    "library": ["library", "package", "npm package", "pypi", "sdk"],
    "static": ["landing page", "static site", "portfolio", "blog"],
}


@dataclass
class TechStack:
    """Detected technology stack from user prompt."""
    backend_framework: Optional[str] = None
    backend_language: Optional[str] = None
    frontend_framework: Optional[str] = None
    frontend_language: Optional[str] = None
    database: Optional[str] = None
    styling: Optional[str] = None
    languages: List[str] = field(default_factory=list)
    extras: List[str] = field(default_factory=list)
    project_type: str = "fullstack"  # cli, api, fullstack, static, mobile, etc.
    is_backend_only: bool = False
    is_frontend_only: bool = False

    @property
    def primary_language(self) -> str:
        """The main language for the project."""
        if self.backend_language:
            return self.backend_language
        if self.frontend_language:
            return self.frontend_language
        if self.languages:
            return self.languages[0]
        return "javascript"

    def to_dict(self) -> dict:
        return {
            "backend_framework": self.backend_framework,
            "backend_language": self.backend_language,
            "frontend_framework": self.frontend_framework,
            "frontend_language": self.frontend_language,
            "database": self.database,
            "styling": self.styling,
            "languages": self.languages,
            "extras": self.extras,
            "project_type": self.project_type,
            "is_backend_only": self.is_backend_only,
            "is_frontend_only": self.is_frontend_only,
        }

    def summary(self) -> str:
        """Human-readable summary of the detected stack."""
        parts = []
        if self.backend_framework:
            parts.append(f"Backend: {self.backend_framework} ({self.backend_language})")
        if self.frontend_framework:
            parts.append(f"Frontend: {self.frontend_framework} ({self.frontend_language})")
        if self.database:
            parts.append(f"Database: {self.database}")
        if self.styling:
            parts.append(f"Styling: {self.styling}")
        if self.extras:
            parts.append(f"Extras: {', '.join(self.extras)}")
        return " | ".join(parts) if parts else "No specific technologies detected"


def detect_stack(prompt: str) -> TechStack:
    """
    Analyze a user prompt and detect the requested technology stack.

    Args:
        prompt: User's project description

    Returns:
        TechStack with detected technologies
    """
    p = prompt.lower()
    stack = TechStack()

    # ── 1. Detect explicit languages ─────────────────────────────
    for keyword, lang in sorted(LANGUAGES.items(), key=lambda x: -len(x[0])):
        if _word_match(p, keyword):
            if lang not in stack.languages:
                stack.languages.append(lang)

    # ── 2. Detect backend framework ──────────────────────────────
    for keyword, (framework, lang) in sorted(BACKEND_FRAMEWORKS.items(), key=lambda x: -len(x[0])):
        if _word_match(p, keyword):
            stack.backend_framework = framework
            stack.backend_language = lang
            if lang not in stack.languages:
                stack.languages.append(lang)
            break

    # ── 3. Detect frontend framework ─────────────────────────────
    for keyword, (framework, lang) in sorted(FRONTEND_FRAMEWORKS.items(), key=lambda x: -len(x[0])):
        if _word_match(p, keyword):
            stack.frontend_framework = framework
            stack.frontend_language = lang
            if lang not in stack.languages:
                stack.languages.append(lang)
            break

    # ── 4. Detect database ───────────────────────────────────────
    for keyword, db in sorted(DATABASES.items(), key=lambda x: -len(x[0])):
        if _word_match(p, keyword):
            stack.database = db
            break

    # ── 5. Detect styling ────────────────────────────────────────
    for keyword, style in sorted(STYLING.items(), key=lambda x: -len(x[0])):
        if _word_match(p, keyword):
            stack.styling = style
            break

    # ── 6. Detect extras ─────────────────────────────────────────
    for keyword, extra in sorted(EXTRAS.items(), key=lambda x: -len(x[0])):
        if _word_match(p, keyword):
            stack.extras.append(extra)

    # ── 7. Detect project type ───────────────────────────────────
    for ptype, keywords in PROJECT_TYPE_PATTERNS.items():
        if any(_word_match(p, kw) for kw in keywords):
            stack.project_type = ptype
            break

    # ── 8. Infer backend-only / frontend-only ────────────────────
    backend_only_hints = ["api only", "backend only", "server only", "no frontend", "rest api", "microservice"]
    frontend_only_hints = ["frontend only", "no backend", "static site", "landing page", "client only"]

    if any(h in p for h in backend_only_hints):
        stack.is_backend_only = True
        stack.project_type = "api"
    elif any(h in p for h in frontend_only_hints):
        stack.is_frontend_only = True
        stack.project_type = "static"

    # ── 9. Infer defaults when nothing explicit ──────────────────
    # If user mentioned a language but no framework, keep it language-centric
    # If nothing at all, we let the LLM decide (no hardcoded default)

    return stack


def _word_match(text: str, keyword: str) -> bool:
    """Check if keyword exists in text as a word (not substring of another word)."""
    # Escape special regex chars in keyword
    escaped = re.escape(keyword)
    pattern = rf'(?<![a-zA-Z0-9_]){escaped}(?![a-zA-Z0-9_])'
    return bool(re.search(pattern, text, re.IGNORECASE))


def get_architect_prompt_for_stack(stack: TechStack) -> str:
    """
    Generate a technology-aware Architect system prompt based on detected stack.
    """
    # Build the stack-specific instructions
    stack_instructions = []

    if stack.backend_framework and stack.frontend_framework:
        stack_instructions.append(
            f"This is a FULL-STACK project using {stack.backend_framework} ({stack.backend_language}) "
            f"for the backend and {stack.frontend_framework} ({stack.frontend_language}) for the frontend."
        )
    elif stack.backend_framework:
        stack_instructions.append(
            f"This is a BACKEND project using {stack.backend_framework} ({stack.backend_language})."
        )
    elif stack.frontend_framework:
        stack_instructions.append(
            f"This is a FRONTEND project using {stack.frontend_framework} ({stack.frontend_language})."
        )

    if stack.database:
        stack_instructions.append(f"Database: {stack.database}")
    if stack.styling:
        stack_instructions.append(f"Styling: {stack.styling}")
    if stack.extras:
        stack_instructions.append(f"Additional tech: {', '.join(stack.extras)}")

    # Build file-type hints
    file_hints = _get_file_hints(stack)

    stack_context = "\n".join(stack_instructions) if stack_instructions else "Infer the best technology stack from the PRD."

    return f"""You are a Senior Software Architect agent. Based on the PRD, design a COMPANY-LEVEL production system.

TECHNOLOGY CONTEXT:
{stack_context}

You MUST output a comprehensive project with MANY files. Think like a real engineering team.

Output ONLY valid JSON:
{{
  "stack": {file_hints["stack_example"]},
  "directory_structure": {file_hints["dir_example"]},
  "component_tree": {{}},
  "data_model": {{"entities": []}},
  "api_endpoints": []
}}

RULES:
- Include AT LEAST 10-20 files for a proper project
- Use the CORRECT file extensions for the detected technology ({', '.join(file_hints['extensions'])})
- Include proper project configuration files ({', '.join(file_hints['config_files'])})
- Include proper directory structure matching the technology conventions
- The project MUST be complete and runnable
- Include build/config files appropriate for the stack
- If fullstack, include BOTH backend and frontend directories
- No markdown. No explanation. JSON only."""


def get_engineer_prompt_for_stack(stack: TechStack, file_path: str) -> str:
    """
    Generate a technology-aware Engineer system prompt based on detected stack.
    """
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    lang_map = {
        "py": "Python", "js": "JavaScript", "jsx": "JavaScript React",
        "ts": "TypeScript", "tsx": "TypeScript React",
        "java": "Java", "kt": "Kotlin", "go": "Go",
        "rs": "Rust", "rb": "Ruby", "php": "PHP",
        "cs": "C#", "swift": "Swift", "dart": "Dart",
        "html": "HTML", "css": "CSS", "scss": "SCSS",
        "json": "JSON", "yaml": "YAML", "yml": "YAML",
        "toml": "TOML", "md": "Markdown", "sql": "SQL",
        "sh": "Shell", "bat": "Batch", "ps1": "PowerShell",
        "xml": "XML", "graphql": "GraphQL", "proto": "Protocol Buffers",
        "ex": "Elixir", "exs": "Elixir", "r": "R",
        "lua": "Lua", "pl": "Perl",
    }
    lang = lang_map.get(ext, "code")

    stack_ctx = ""
    if stack.backend_framework:
        stack_ctx += f"Backend: {stack.backend_framework} ({stack.backend_language}). "
    if stack.frontend_framework:
        stack_ctx += f"Frontend: {stack.frontend_framework} ({stack.frontend_language}). "
    if stack.database:
        stack_ctx += f"Database: {stack.database}. "
    if stack.styling:
        stack_ctx += f"Styling: {stack.styling}. "

    return f"""You are a Senior Software Engineer at a top tech company. Write the COMPLETE contents of the file '{file_path}'.

TECHNOLOGY CONTEXT: {stack_ctx or 'Use best practices for the file type.'}
LANGUAGE: {lang}

CRITICAL RULES:
- Write PRODUCTION-READY, COMPANY-LEVEL code
- NO markdown, NO explanations, NO code fences (```)
- Output ONLY the raw file content — nothing before or after
- Include ALL imports, exports, types, and logic
- Write REAL functionality, not placeholders or TODOs
- Use modern best practices for {lang}
- Follow the conventions of the detected framework/language
- Make it look professional and well-structured
- Include proper error handling
- Include appropriate comments for complex logic"""


def get_fallback_architecture(stack: TechStack, prompt: str) -> dict:
    """
    Generate a fallback architecture dict for when LLM fails, based on detected stack.
    """
    # Python backends
    if stack.backend_language == "python":
        if stack.backend_framework == "Django":
            return _django_fallback(stack, prompt)
        elif stack.backend_framework == "Flask":
            return _flask_fallback(stack, prompt)
        else:
            return _fastapi_fallback(stack, prompt)

    # JavaScript/TypeScript backends
    if stack.backend_language in ("javascript", "typescript"):
        if stack.backend_framework == "NestJS":
            return _nestjs_fallback(stack, prompt)
        else:
            return _express_fallback(stack, prompt)

    # Go
    if stack.backend_language == "go":
        return _go_fallback(stack, prompt)

    # Java
    if stack.backend_language == "java":
        return _java_spring_fallback(stack, prompt)

    # Frontend-only
    if stack.is_frontend_only or (stack.frontend_framework and not stack.backend_framework):
        return _frontend_only_fallback(stack, prompt)

    # CLI / scripts (python default)
    if stack.project_type == "cli":
        return _cli_fallback(stack, prompt)

    # Default: React + Vite (the existing behavior)
    return _react_vite_fallback(stack, prompt)


# ── File hint helpers ────────────────────────────────────────────────────────

def _get_file_hints(stack: TechStack) -> dict:
    """Get file extension and config file hints for a tech stack."""
    hints = {
        "extensions": [],
        "config_files": [],
        "stack_example": "{}",
        "dir_example": "[]",
    }

    bl = stack.backend_language or ""
    fl = stack.frontend_language or ""
    bf = stack.backend_framework or ""
    ff = stack.frontend_framework or ""

    # Extensions
    lang_exts = {
        "python": [".py"], "javascript": [".js", ".jsx"], "typescript": [".ts", ".tsx"],
        "java": [".java"], "go": [".go"], "rust": [".rs"],
        "ruby": [".rb"], "php": [".php"], "csharp": [".cs"],
        "dart": [".dart"], "kotlin": [".kt"], "swift": [".swift"],
    }
    for lang in set([bl, fl]):
        hints["extensions"].extend(lang_exts.get(lang, []))
    if not hints["extensions"]:
        hints["extensions"] = [".js", ".jsx", ".css", ".html"]

    # Config files by framework
    config_map = {
        "FastAPI": ["requirements.txt", ".env", "main.py"],
        "Django": ["requirements.txt", "manage.py", "settings.py"],
        "Flask": ["requirements.txt", ".env", "app.py"],
        "Express": ["package.json", ".env", "tsconfig.json"],
        "NestJS": ["package.json", "tsconfig.json", "nest-cli.json"],
        "Spring Boot": ["pom.xml", "application.properties"],
        "Gin": ["go.mod", "go.sum", "main.go"],
        "React": ["package.json", "vite.config.js", "index.html"],
        "Next.js": ["package.json", "next.config.js", "tsconfig.json"],
        "Vue": ["package.json", "vite.config.js", "index.html"],
        "Angular": ["package.json", "angular.json", "tsconfig.json"],
        "Svelte": ["package.json", "svelte.config.js", "vite.config.js"],
    }
    for fw in [bf, ff]:
        hints["config_files"].extend(config_map.get(fw, []))
    if not hints["config_files"]:
        hints["config_files"] = ["package.json", "README.md"]

    # Build example JSON strings for the prompt
    stack_dict = {}
    if bf:
        stack_dict["backend"] = f"{bf}"
    if ff:
        stack_dict["frontend"] = f"{ff}"
    if stack.styling:
        stack_dict["styling"] = stack.styling
    if stack.database:
        stack_dict["database"] = stack.database
    if not stack_dict:
        stack_dict = {"frontend": "React + Vite", "styling": "CSS"}

    import json
    hints["stack_example"] = json.dumps(stack_dict)
    hints["dir_example"] = json.dumps(hints["config_files"][:5] + ["...more files..."])

    return hints


# ── Fallback architectures ───────────────────────────────────────────────────

def _fastapi_fallback(stack: TechStack, prompt: str) -> dict:
    files = [
        "requirements.txt", "main.py", "config.py",
        "routers/__init__.py", "routers/api.py",
        "models/__init__.py", "models/schemas.py",
        "services/__init__.py", "services/logic.py",
        "tests/test_api.py", ".env.example", "README.md",
    ]
    if stack.frontend_framework:
        files.extend(_frontend_files(stack))
    d = {"stack": {"backend": "FastAPI", "language": "Python"}, "directory_structure": files}
    if stack.database:
        d["stack"]["database"] = stack.database
        files.insert(3, "database.py")
    if stack.frontend_framework:
        d["stack"]["frontend"] = stack.frontend_framework
    return d


def _django_fallback(stack: TechStack, prompt: str) -> dict:
    files = [
        "requirements.txt", "manage.py",
        "project/settings.py", "project/urls.py", "project/wsgi.py", "project/__init__.py",
        "app/__init__.py", "app/models.py", "app/views.py", "app/urls.py",
        "app/serializers.py", "app/admin.py", "app/tests.py",
        "templates/base.html", "README.md",
    ]
    if stack.frontend_framework:
        files.extend(_frontend_files(stack))
    d = {"stack": {"backend": "Django", "language": "Python"}, "directory_structure": files}
    if stack.database:
        d["stack"]["database"] = stack.database
    return d


def _flask_fallback(stack: TechStack, prompt: str) -> dict:
    files = [
        "requirements.txt", "app.py", "config.py",
        "routes/__init__.py", "routes/api.py",
        "models/__init__.py", "models/db.py",
        "templates/index.html", "static/style.css",
        "tests/test_app.py", ".env.example", "README.md",
    ]
    if stack.frontend_framework:
        files.extend(_frontend_files(stack))
    d = {"stack": {"backend": "Flask", "language": "Python"}, "directory_structure": files}
    if stack.database:
        d["stack"]["database"] = stack.database
    return d


def _express_fallback(stack: TechStack, prompt: str) -> dict:
    ext = ".ts" if stack.backend_language == "typescript" else ".js"
    files = [
        "package.json", f"src/index{ext}", f"src/app{ext}",
        f"src/routes/api{ext}", f"src/middleware/auth{ext}",
        f"src/controllers/main{ext}", f"src/models/schema{ext}",
        f"src/config/db{ext}", "tests/api.test{ext}",
        ".env.example", "README.md",
    ]
    if stack.backend_language == "typescript":
        files.insert(1, "tsconfig.json")
    if stack.frontend_framework:
        files.extend(_frontend_files(stack))
    d = {"stack": {"backend": "Express", "language": stack.backend_language or "javascript"}, "directory_structure": files}
    if stack.database:
        d["stack"]["database"] = stack.database
    return d


def _nestjs_fallback(stack: TechStack, prompt: str) -> dict:
    files = [
        "package.json", "tsconfig.json", "nest-cli.json",
        "src/main.ts", "src/app.module.ts", "src/app.controller.ts", "src/app.service.ts",
        "src/items/items.module.ts", "src/items/items.controller.ts",
        "src/items/items.service.ts", "src/items/dto/create-item.dto.ts",
        "test/app.e2e-spec.ts", ".env.example", "README.md",
    ]
    if stack.frontend_framework:
        files.extend(_frontend_files(stack))
    d = {"stack": {"backend": "NestJS", "language": "TypeScript"}, "directory_structure": files}
    if stack.database:
        d["stack"]["database"] = stack.database
    return d


def _go_fallback(stack: TechStack, prompt: str) -> dict:
    fw = stack.backend_framework or "Gin"
    files = [
        "go.mod", "go.sum", "main.go",
        "internal/handler/handler.go", "internal/handler/routes.go",
        "internal/model/model.go", "internal/service/service.go",
        "internal/repository/repository.go", "internal/config/config.go",
        "cmd/server/main.go", "Makefile", ".env.example", "README.md",
    ]
    if stack.frontend_framework:
        files.extend(_frontend_files(stack))
    d = {"stack": {"backend": fw, "language": "Go"}, "directory_structure": files}
    if stack.database:
        d["stack"]["database"] = stack.database
    return d


def _java_spring_fallback(stack: TechStack, prompt: str) -> dict:
    files = [
        "pom.xml", "src/main/resources/application.properties",
        "src/main/java/com/app/Application.java",
        "src/main/java/com/app/controller/ApiController.java",
        "src/main/java/com/app/model/Entity.java",
        "src/main/java/com/app/service/AppService.java",
        "src/main/java/com/app/repository/EntityRepository.java",
        "src/main/java/com/app/config/AppConfig.java",
        "src/test/java/com/app/ApplicationTests.java",
        "README.md",
    ]
    if stack.frontend_framework:
        files.extend(_frontend_files(stack))
    d = {"stack": {"backend": "Spring Boot", "language": "Java"}, "directory_structure": files}
    if stack.database:
        d["stack"]["database"] = stack.database
    return d


def _react_vite_fallback(stack: TechStack, prompt: str) -> dict:
    return {
        "stack": {"frontend": "React + Vite", "styling": stack.styling or "CSS"},
        "directory_structure": [
            "package.json", "vite.config.js", "index.html",
            "src/main.jsx", "src/App.jsx", "src/App.css", "src/index.css",
            "src/components/Header.jsx", "src/components/Header.css",
            "src/components/Footer.jsx",
            "src/pages/Home.jsx", "src/hooks/useLocalStorage.js",
            "src/utils/helpers.js", "src/styles/variables.css",
        ],
    }


def _frontend_only_fallback(stack: TechStack, prompt: str) -> dict:
    ff = stack.frontend_framework or "React"
    if ff in ("Next.js",):
        return {
            "stack": {"frontend": "Next.js", "language": "TypeScript"},
            "directory_structure": [
                "package.json", "next.config.js", "tsconfig.json",
                "app/layout.tsx", "app/page.tsx", "app/globals.css",
                "components/Header.tsx", "components/Footer.tsx",
                "lib/utils.ts", "public/favicon.ico", "README.md",
            ],
        }
    elif ff in ("Vue",):
        return {
            "stack": {"frontend": "Vue + Vite", "styling": stack.styling or "CSS"},
            "directory_structure": [
                "package.json", "vite.config.js", "index.html",
                "src/main.js", "src/App.vue", "src/style.css",
                "src/components/Header.vue", "src/components/Footer.vue",
                "src/views/Home.vue", "src/router/index.js",
                "README.md",
            ],
        }
    elif ff in ("Angular",):
        return {
            "stack": {"frontend": "Angular", "styling": stack.styling or "CSS"},
            "directory_structure": [
                "package.json", "angular.json", "tsconfig.json",
                "src/main.ts", "src/index.html", "src/styles.css",
                "src/app/app.component.ts", "src/app/app.component.html",
                "src/app/app.component.css", "src/app/app.module.ts",
                "src/app/components/header/header.component.ts",
                "README.md",
            ],
        }
    elif ff in ("Svelte", "SvelteKit"):
        return {
            "stack": {"frontend": "SvelteKit", "styling": stack.styling or "CSS"},
            "directory_structure": [
                "package.json", "svelte.config.js", "vite.config.js",
                "src/routes/+page.svelte", "src/routes/+layout.svelte",
                "src/lib/components/Header.svelte", "src/app.css",
                "static/favicon.png", "README.md",
            ],
        }
    # Default: React + Vite
    return _react_vite_fallback(stack, prompt)


def _cli_fallback(stack: TechStack, prompt: str) -> dict:
    lang = stack.primary_language
    if lang == "python":
        return {
            "stack": {"language": "Python", "type": "CLI"},
            "directory_structure": [
                "requirements.txt", "setup.py",
                "cli/__init__.py", "cli/main.py", "cli/commands.py",
                "cli/utils.py", "tests/test_cli.py", "README.md",
            ],
        }
    elif lang == "go":
        return {
            "stack": {"language": "Go", "type": "CLI"},
            "directory_structure": [
                "go.mod", "main.go",
                "cmd/root.go", "cmd/run.go",
                "internal/config.go", "internal/logic.go",
                "Makefile", "README.md",
            ],
        }
    elif lang == "rust":
        return {
            "stack": {"language": "Rust", "type": "CLI"},
            "directory_structure": [
                "Cargo.toml", "src/main.rs", "src/cli.rs",
                "src/commands.rs", "src/utils.rs",
                "tests/integration.rs", "README.md",
            ],
        }
    else:
        return {
            "stack": {"language": lang.capitalize(), "type": "CLI"},
            "directory_structure": [
                "package.json", "src/index.js", "src/cli.js",
                "src/commands.js", "src/utils.js",
                "tests/cli.test.js", "README.md",
            ],
        }


def _frontend_files(stack: TechStack) -> list:
    """Additional frontend files when paired with a backend."""
    ff = stack.frontend_framework or "React"
    if ff == "Vue":
        return [
            "frontend/package.json", "frontend/vite.config.js", "frontend/index.html",
            "frontend/src/main.js", "frontend/src/App.vue", "frontend/src/style.css",
        ]
    elif ff == "Angular":
        return [
            "frontend/package.json", "frontend/angular.json",
            "frontend/src/main.ts", "frontend/src/index.html",
            "frontend/src/app/app.component.ts",
        ]
    elif ff in ("Next.js",):
        return [
            "frontend/package.json", "frontend/next.config.js",
            "frontend/app/layout.tsx", "frontend/app/page.tsx",
        ]
    elif ff in ("Svelte", "SvelteKit"):
        return [
            "frontend/package.json", "frontend/svelte.config.js",
            "frontend/src/routes/+page.svelte",
        ]
    else:  # React default
        return [
            "frontend/package.json", "frontend/vite.config.js", "frontend/index.html",
            "frontend/src/main.jsx", "frontend/src/App.jsx", "frontend/src/index.css",
        ]
