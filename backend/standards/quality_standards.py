"""
S-Class Quality Standards — VibeCober

Defines what production-quality means for generated projects.
Real software companies follow these standards. So should we.

This module provides:
1. Quality tier definitions (S/A/B/C)
2. File structure requirements per project type
3. Code quality checklists
4. Scoring functions for generated output
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


# ═════════════════════════════════════════════════════════════════════════════
# QUALITY TIERS
# ═════════════════════════════════════════════════════════════════════════════

class QualityTier(str, Enum):
    S = "S"   # Production-grade, company-level
    A = "A"   # Professional, deployable
    B = "B"   # Functional, needs polish
    C = "C"   # MVP / prototype only


# ═════════════════════════════════════════════════════════════════════════════
# S-CLASS PROJECT REQUIREMENTS
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class ProjectRequirements:
    """What an S-class project must have."""

    # ── Structure ──
    min_files: int = 25
    max_empty_files: int = 0
    requires_readme: bool = True
    requires_gitignore: bool = True
    requires_env_example: bool = True
    requires_license: bool = False

    # ── Frontend Requirements ──
    frontend_typescript: bool = True            # TypeScript not JS
    frontend_component_library: bool = True     # shadcn/ui, Radix, etc.
    frontend_state_management: bool = True      # Zustand, TanStack Query
    frontend_routing: bool = True               # React Router / Next.js routing
    frontend_error_boundaries: bool = True
    frontend_loading_states: bool = True
    frontend_responsive: bool = True
    frontend_dark_mode: bool = False
    frontend_seo: bool = True
    frontend_accessibility: bool = True
    frontend_code_splitting: bool = True
    frontend_form_validation: bool = True

    # ── Backend Requirements ──
    backend_typed: bool = True                  # Type hints everywhere
    backend_error_handling: bool = True         # Proper HTTP error responses
    backend_validation: bool = True             # Pydantic / Zod schemas
    backend_middleware: bool = True             # CORS, rate limiting, logging
    backend_health_check: bool = True
    backend_env_config: bool = True             # Environment-based config
    backend_structured_logging: bool = True
    backend_api_versioning: bool = True

    # ── Security ──
    security_auth_tokens: bool = True
    security_password_hashing: bool = True
    security_rate_limiting: bool = True
    security_input_sanitization: bool = True
    security_cors_configured: bool = True
    security_no_hardcoded_secrets: bool = True

    # ── Testing ──
    testing_unit: bool = True
    testing_integration: bool = False
    testing_e2e: bool = False
    testing_config_files: bool = True           # vitest.config, pytest.ini

    # ── DevOps ──
    devops_dockerfile: bool = True
    devops_docker_compose: bool = True
    devops_ci_cd: bool = True                   # GitHub Actions
    devops_linting: bool = True                 # ESLint, Ruff/Black
    devops_formatting: bool = True              # Prettier, Black

    # ── Documentation ──
    docs_readme: bool = True
    docs_api_docs: bool = True                  # OpenAPI/Swagger
    docs_setup_guide: bool = True
    docs_architecture: bool = True


# ═════════════════════════════════════════════════════════════════════════════
# S-CLASS FILE STRUCTURE STANDARDS
# ═════════════════════════════════════════════════════════════════════════════

# What an SSS-class React frontend looks like (platform architecture)
SSS_CLASS_FRONTEND_STRUCTURE = {
    "config_files": [
        "package.json",
        "tsconfig.json",
        "tsconfig.app.json",
        "tsconfig.node.json",
        "vite.config.ts",
        "tailwind.config.ts",
        "postcss.config.js",
        "eslint.config.js",
        ".prettierrc",
        ".env.example",
        "components.json",
        "index.html",
        "vitest.config.ts",
    ],
    "source_structure": {
        "src/": {
            "app/": {
                "App.tsx": "Application shell — composes providers + routes",
                "providers/": "QueryProvider, ThemeProvider, ErrorBoundaryProvider",
                "routes/": "ProtectedRoute, route guards",
                "layouts/": "AppLayout, DashboardLayout",
            },
            "core/": {
                "config/": "Environment config with Zod validation",
                "logger/": "Structured logging with redaction",
                "error/": "Typed errors (AppError, ApiError, NetworkError)",
                "performance/": "Perf measurement, Web Vitals",
                "constants/": "ROUTES, API_ENDPOINTS, QUERY_KEYS, STORAGE_KEYS",
            },
            "infrastructure/": {
                "http/": "apiClient with interceptors, retry, backoff",
                "websocket/": "WebSocket client with auto-reconnect",
                "queryClient.ts": "React Query utilities",
            },
            "features/": {
                "auth/": "Login, Register, auth store (isolated)",
                "dashboard/": "Stats, activity feed (isolated)",
                "settings/": "Profile, preferences (isolated)",
                "<domain>/": "Each feature has: components/ hooks/ api/ types.ts index.ts",
            },
            "shared/": {
                "ui/": "Button, Input, Card, Dialog, Badge, Skeleton, LoadingScreen",
                "components/": "Header, Footer, FeatureErrorBoundary, NotFound",
                "hooks/": "useDebounce, useLocalStorage, useMediaQuery",
                "utils/": "cn, format, validators",
                "types/": "Shared interfaces (User, ApiResponse, PaginatedResponse)",
            },
            "styles/": "Design tokens (CSS variables), globals.css",
        },
    },
    "critical_files": [
        "src/main.tsx",
        "src/app/App.tsx",
        "src/app/providers/QueryProvider.tsx",
        "src/app/providers/ThemeProvider.tsx",
        "src/app/providers/ErrorBoundaryProvider.tsx",
        "src/core/config/index.ts",
        "src/core/logger/index.ts",
        "src/core/error/index.ts",
        "src/core/constants/index.ts",
        "src/infrastructure/http/apiClient.ts",
        "src/infrastructure/http/interceptors.ts",
        "src/features/auth/index.ts",
        "src/features/auth/hooks/useAuthStore.ts",
        "src/shared/ui/Button.tsx",
        "src/shared/utils/cn.ts",
        "src/shared/types/index.ts",
        "src/styles/globals.css",
    ],
    "engineering_constitution": [
        "No business logic inside components",
        "All API calls through centralized client",
        "Global error boundary required",
        "Strict typing everywhere (no any)",
        "No cross-feature imports (barrel exports only)",
        "Lazy-load features by default",
        "Centralized state: React Query + Zustand",
        "Structured logging with context",
        "No magic strings — constants registry",
        "Config-driven environment handling",
    ],
}

# Legacy S-class structure (kept for backward compat)
SCLASS_FRONTEND_STRUCTURE = {
    "config_files": [
        "package.json",
        "tsconfig.json",
        "tsconfig.app.json",
        "vite.config.ts",
        "tailwind.config.ts",
        "postcss.config.js",
        "eslint.config.js",
        ".prettierrc",
        "components.json",
        "index.html",
    ],
    "source_structure": {
        "src/": {
            "components/": {
                "ui/": "Reusable UI primitives (Button, Card, Input, Dialog, etc.)",
                "layout/": "Layout components (Header, Footer, Sidebar, Navigation)",
                "forms/": "Form components with validation",
                "feature-specific/": "Domain components for each feature",
            },
            "pages/": "Route-level page components",
            "hooks/": "Custom React hooks (useAuth, useApi, useDebounce, etc.)",
            "lib/": "Utility functions, API client, constants",
            "stores/": "State management (Zustand stores)",
            "types/": "TypeScript type definitions",
            "styles/": "Global styles, theme config",
            "assets/": "Static assets (images, icons, fonts)",
        },
    },
    "critical_files": [
        "src/main.tsx",
        "src/App.tsx",
        "src/App.css",
        "src/index.css",
        "src/vite-env.d.ts",
        "src/lib/api-client.ts",
        "src/lib/utils.ts",
        "src/hooks/use-auth.ts",
        "src/components/ui/button.tsx",
        "src/types/index.ts",
    ],
}

# What a REAL Python backend looks like
SCLASS_BACKEND_STRUCTURE = {
    "config_files": [
        "requirements.txt",
        "pyproject.toml",       # or setup.py
        ".env.example",
        "alembic.ini",          # if using migrations
    ],
    "source_structure": {
        "app/": {
            "api/": {
                "v1/": "Versioned API routes",
                "deps.py": "Dependency injection",
            },
            "core/": "Config, security, settings",
            "models/": "SQLAlchemy/Pydantic models",
            "schemas/": "Request/Response Pydantic schemas",
            "services/": "Business logic layer",
            "middleware/": "Custom middleware (logging, rate limiting)",
            "utils/": "Utility functions",
        },
    },
    "critical_files": [
        "app/main.py",
        "app/core/config.py",
        "app/core/security.py",
        "app/api/deps.py",
        "app/models/__init__.py",
        "app/schemas/__init__.py",
    ],
}


# ═════════════════════════════════════════════════════════════════════════════
# QUALITY SCORING
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class QualityScore:
    """Quality assessment for a generated project."""
    tier: QualityTier
    total_score: int              # 0-100
    file_count: int
    structure_score: int          # 0-25
    code_quality_score: int       # 0-25
    security_score: int           # 0-25
    completeness_score: int       # 0-25
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier.value,
            "total_score": self.total_score,
            "file_count": self.file_count,
            "breakdown": {
                "structure": self.structure_score,
                "code_quality": self.code_quality_score,
                "security": self.security_score,
                "completeness": self.completeness_score,
            },
            "issues": self.issues,
            "recommendations": self.recommendations,
        }


def score_project(
    files: Dict[str, str],
    requirements: Optional[ProjectRequirements] = None,
) -> QualityScore:
    """
    Score a generated project against S-class standards.

    Args:
        files: Dict mapping file paths to contents
        requirements: Standards to score against (defaults to S-class)

    Returns:
        QualityScore with tier, breakdown, and recommendations
    """
    if requirements is None:
        requirements = ProjectRequirements()

    issues = []
    recommendations = []
    file_paths = list(files.keys())
    file_count = len(file_paths)

    # ── Structure Score (0-25) ──
    structure_score = 0

    if file_count >= requirements.min_files:
        structure_score += 8
    elif file_count >= 15:
        structure_score += 5
        issues.append(f"Only {file_count} files (S-class needs {requirements.min_files}+)")
    else:
        structure_score += 2
        issues.append(f"Only {file_count} files — far below S-class")

    # Check for proper directory depth
    has_nested = any(p.count("/") >= 2 for p in file_paths)
    if has_nested:
        structure_score += 5
    else:
        issues.append("Flat file structure — needs proper directory hierarchy")

    # Check for separation of concerns
    has_components = any("component" in p.lower() for p in file_paths)
    has_pages = any("page" in p.lower() for p in file_paths)
    has_hooks = any("hook" in p.lower() for p in file_paths)
    has_utils = any("util" in p.lower() or "lib" in p.lower() for p in file_paths)
    has_types = any("type" in p.lower() for p in file_paths)

    soc_count = sum([has_components, has_pages, has_hooks, has_utils, has_types])
    structure_score += min(soc_count * 2, 8)
    if soc_count < 3:
        issues.append("Missing separation of concerns (components/pages/hooks/utils/types)")

    # Config files
    config_extensions = {".json", ".ts", ".js", ".yml", ".yaml", ".toml", ".ini", ".cfg"}
    has_config = any(
        any(p.endswith(ext) for ext in config_extensions)
        and ("config" in p.lower() or "tsconfig" in p.lower() or "eslint" in p.lower())
        for p in file_paths
    )
    if has_config:
        structure_score += 4
    else:
        issues.append("Missing configuration files (tsconfig, eslint, etc.)")

    # ── Code Quality Score (0-25) ──
    code_quality_score = 0
    total_content = "\n".join(files.values())

    # TypeScript usage
    ts_files = [p for p in file_paths if p.endswith((".ts", ".tsx"))]
    js_files = [p for p in file_paths if p.endswith((".js", ".jsx"))]
    if ts_files and len(ts_files) >= len(js_files):
        code_quality_score += 5
    elif ts_files:
        code_quality_score += 3
        recommendations.append("Convert JS files to TypeScript for type safety")
    else:
        if js_files:
            issues.append("No TypeScript — S-class projects use TypeScript")

    # Proper imports/exports
    if "import " in total_content or "from " in total_content:
        code_quality_score += 3

    # Error handling
    error_patterns = ["try", "catch", "except", "throw", "raise", "Error"]
    error_count = sum(1 for p in error_patterns if p in total_content)
    code_quality_score += min(error_count, 5)
    if error_count < 2:
        issues.append("Insufficient error handling")

    # Type annotations
    type_patterns = ["interface ", "type ", ": str", ": int", ": Dict", "-> ", "Props"]
    type_count = sum(1 for p in type_patterns if p in total_content)
    code_quality_score += min(type_count * 2, 6)

    # No TODOs or placeholders
    placeholder_count = total_content.lower().count("todo") + total_content.lower().count("placeholder")
    if placeholder_count == 0:
        code_quality_score += 3
    elif placeholder_count <= 3:
        code_quality_score += 1
        issues.append(f"{placeholder_count} TODO/placeholder found — implement all features")
    else:
        issues.append(f"{placeholder_count} TODOs/placeholders — incomplete implementation")

    # Modern patterns
    modern_patterns = ["async ", "await ", "useState", "useEffect", "useCallback", "useMemo"]
    modern_count = sum(1 for p in modern_patterns if p in total_content)
    code_quality_score += min(modern_count, 3)

    # ── Security Score (0-25) ──
    security_score = 0

    # No hardcoded secrets
    secret_patterns = [
        "your-secret-key", "change-in-production", "password123",
        "sk-", "pk_test_", "sk_test_",
    ]
    hardcoded_secrets = sum(1 for s in secret_patterns if s in total_content)
    if hardcoded_secrets == 0:
        security_score += 8
    else:
        issues.append(f"{hardcoded_secrets} hardcoded secrets found — use environment variables")

    # Environment variables used
    if "os.environ" in total_content or "process.env" in total_content or ".env" in total_content:
        security_score += 5
    else:
        issues.append("No environment variable usage — secrets at risk")

    # CORS configured
    if "cors" in total_content.lower():
        security_score += 4
    
    # Input validation
    if "pydantic" in total_content.lower() or "zod" in total_content.lower() or "schema" in total_content.lower():
        security_score += 4

    # Auth patterns
    auth_patterns = ["bearer", "jwt", "bcrypt", "hash", "token"]
    auth_count = sum(1 for p in auth_patterns if p.lower() in total_content.lower())
    security_score += min(auth_count * 2, 4)

    # ── Completeness Score (0-25) ──
    completeness_score = 0

    # Has README
    if any("readme" in p.lower() for p in file_paths):
        completeness_score += 3

    # Has .gitignore
    if any(".gitignore" in p.lower() for p in file_paths):
        completeness_score += 2

    # Has tests
    if any("test" in p.lower() for p in file_paths):
        completeness_score += 4
    else:
        issues.append("No test files")

    # Has Docker config
    if any("docker" in p.lower() for p in file_paths):
        completeness_score += 3
    else:
        recommendations.append("Add Docker configuration for deployment")

    # Has CI/CD
    if any("github" in p.lower() or "ci" in p.lower() for p in file_paths):
        completeness_score += 3
    else:
        recommendations.append("Add CI/CD pipeline (GitHub Actions)")

    # Has proper package management
    if any("package.json" in p or "requirements.txt" in p or "pyproject.toml" in p for p in file_paths):
        completeness_score += 3

    # Has env example
    if any(".env" in p.lower() and "example" in p.lower() for p in file_paths):
        completeness_score += 2

    # Has API docs or Swagger
    if "swagger" in total_content.lower() or "openapi" in total_content.lower() or "/docs" in total_content:
        completeness_score += 3

    # Lint / format configs
    if any("eslint" in p.lower() or "prettier" in p.lower() or "ruff" in p.lower() for p in file_paths):
        completeness_score += 2
    else:
        recommendations.append("Add linting and formatting configuration")

    # ── SSS-Class Architecture Bonus (0-10) ──
    # Reward projects that follow the SSS-class platform architecture
    sss_bonus = 0
    sss_critical = SSS_CLASS_FRONTEND_STRUCTURE.get("critical_files", [])
    matched_critical = sum(
        1 for cf in sss_critical
        if any(p.endswith(cf) or cf in p for p in file_paths)
    )
    if sss_critical and matched_critical >= len(sss_critical) * 0.7:
        sss_bonus += 5  # Most critical SSS-class files present
    if any("infrastructure/http" in p for p in file_paths):
        sss_bonus += 2  # Centralized HTTP client layer
    if any("core/config" in p for p in file_paths):
        sss_bonus += 1  # Config-driven env handling
    if any("core/logger" in p for p in file_paths):
        sss_bonus += 1  # Structured logging
    if any("core/error" in p for p in file_paths):
        sss_bonus += 1  # Typed error hierarchy

    # ── Calculate Final Score & Tier ──
    total_score = structure_score + code_quality_score + security_score + completeness_score + sss_bonus

    if total_score >= 85:
        tier = QualityTier.S
    elif total_score >= 65:
        tier = QualityTier.A
    elif total_score >= 45:
        tier = QualityTier.B
    else:
        tier = QualityTier.C

    return QualityScore(
        tier=tier,
        total_score=total_score,
        file_count=file_count,
        structure_score=structure_score,
        code_quality_score=code_quality_score,
        security_score=security_score,
        completeness_score=completeness_score,
        issues=issues,
        recommendations=recommendations,
    )


# ═════════════════════════════════════════════════════════════════════════════
# S-CLASS ARCHITECTURE BLUEPRINTS
# ═════════════════════════════════════════════════════════════════════════════

def get_sclass_file_plan(
    project_type: str,
    features: List[str],
    tech_stack: Dict[str, str],
) -> List[str]:
    """
    Generate an S-class file plan based on project requirements.

    Returns a comprehensive list of files that a real software team
    would create for this type of project.
    """
    files = []

    backend_fw = tech_stack.get("backend", "FastAPI").lower()
    frontend_fw = tech_stack.get("frontend", "React").lower()
    database = tech_stack.get("database", "PostgreSQL").lower()
    styling = tech_stack.get("styling", "Tailwind CSS").lower()

    # ── Root Config ──
    files.extend([
        "README.md",
        ".gitignore",
        ".env.example",
        "docker-compose.yml",
        "docker-compose.prod.yml",
        "Makefile",
        ".github/workflows/ci.yml",
        ".github/workflows/deploy.yml",
    ])

    # ── Backend Files ──
    if backend_fw != "none":
        if "python" in backend_fw or "fastapi" in backend_fw or "django" in backend_fw or "flask" in backend_fw:
            files.extend(_python_backend_files(features, backend_fw, database))
        elif "express" in backend_fw or "node" in backend_fw or "nest" in backend_fw:
            files.extend(_node_backend_files(features, backend_fw))
        elif "go" in backend_fw or "gin" in backend_fw:
            files.extend(_go_backend_files(features))
        elif "spring" in backend_fw or "java" in backend_fw:
            files.extend(_java_backend_files(features))
        else:
            files.extend(_python_backend_files(features, "fastapi", database))

    # ── Frontend Files ──
    if frontend_fw != "none":
        if "next" in frontend_fw:
            files.extend(_nextjs_frontend_files(features, styling))
        elif "vue" in frontend_fw:
            files.extend(_vue_frontend_files(features, styling))
        elif "angular" in frontend_fw:
            files.extend(_angular_frontend_files(features))
        elif "svelte" in frontend_fw:
            files.extend(_svelte_frontend_files(features, styling))
        else:
            files.extend(_react_frontend_files(features, styling))

    return files


def _python_backend_files(features: List[str], framework: str, database: str) -> List[str]:
    """Generate Python backend file list."""
    files = [
        # Core
        "backend/main.py",
        "backend/__init__.py",
        "backend/requirements.txt",
        "backend/Dockerfile",
        "backend/.env.example",

        # Config
        "backend/core/__init__.py",
        "backend/core/config.py",
        "backend/core/security.py",
        "backend/core/database.py",
        "backend/core/exceptions.py",
        "backend/core/logging_config.py",

        # API
        "backend/api/__init__.py",
        "backend/api/deps.py",
        "backend/api/v1/__init__.py",
        "backend/api/v1/router.py",

        # Middleware
        "backend/middleware/__init__.py",
        "backend/middleware/rate_limit.py",
        "backend/middleware/logging.py",
        "backend/middleware/error_handler.py",

        # Schemas
        "backend/schemas/__init__.py",
        "backend/schemas/common.py",

        # Services
        "backend/services/__init__.py",

        # Utils
        "backend/utils/__init__.py",
        "backend/utils/helpers.py",

        # Tests
        "backend/tests/__init__.py",
        "backend/tests/conftest.py",
        "backend/tests/test_health.py",
    ]

    # Auth feature
    if any(f in " ".join(features).lower() for f in ["auth", "login", "user", "signup", "register"]):
        files.extend([
            "backend/api/v1/auth.py",
            "backend/models/user.py",
            "backend/schemas/auth.py",
            "backend/schemas/user.py",
            "backend/services/auth_service.py",
            "backend/services/user_service.py",
            "backend/tests/test_auth.py",
        ])
    
    # Database models for features
    feature_lower = " ".join(features).lower()
    if any(f in feature_lower for f in ["post", "blog", "article", "content"]):
        files.extend([
            "backend/models/post.py",
            "backend/schemas/post.py",
            "backend/api/v1/posts.py",
            "backend/services/post_service.py",
        ])
    if any(f in feature_lower for f in ["product", "item", "catalog", "shop", "store"]):
        files.extend([
            "backend/models/product.py",
            "backend/schemas/product.py",
            "backend/api/v1/products.py",
            "backend/services/product_service.py",
        ])
    if any(f in feature_lower for f in ["chat", "message", "inbox"]):
        files.extend([
            "backend/models/message.py",
            "backend/schemas/message.py",
            "backend/api/v1/messages.py",
            "backend/services/message_service.py",
        ])
    if any(f in feature_lower for f in ["payment", "billing", "subscription", "stripe"]):
        files.extend([
            "backend/services/payment_service.py",
            "backend/api/v1/payments.py",
            "backend/schemas/payment.py",
        ])
    if any(f in feature_lower for f in ["notification", "alert", "email"]):
        files.extend([
            "backend/services/notification_service.py",
            "backend/api/v1/notifications.py",
        ])
    if any(f in feature_lower for f in ["upload", "file", "image", "media"]):
        files.extend([
            "backend/services/storage_service.py",
            "backend/api/v1/uploads.py",
        ])

    # Always add models init
    files.append("backend/models/__init__.py")

    # Database migrations
    if "postgresql" in database or "mysql" in database or "sqlite" in database:
        files.extend([
            "backend/alembic.ini",
            "backend/migrations/env.py",
            "backend/migrations/versions/.gitkeep",
        ])

    return files


def _node_backend_files(features: List[str], framework: str) -> List[str]:
    """Generate Node.js backend file list."""
    ext = ".ts"
    files = [
        "backend/package.json",
        "backend/tsconfig.json",
        "backend/Dockerfile",
        "backend/.env.example",
        f"backend/src/index{ext}",
        f"backend/src/app{ext}",
        f"backend/src/config/index{ext}",
        f"backend/src/config/database{ext}",
        f"backend/src/middleware/errorHandler{ext}",
        f"backend/src/middleware/auth{ext}",
        f"backend/src/middleware/rateLimit{ext}",
        f"backend/src/middleware/logger{ext}",
        f"backend/src/routes/index{ext}",
        f"backend/src/routes/health{ext}",
        f"backend/src/utils/helpers{ext}",
        f"backend/src/types/index{ext}",
        f"backend/tests/health.test{ext}",
    ]

    feature_lower = " ".join(features).lower()
    if any(f in feature_lower for f in ["auth", "login", "user"]):
        files.extend([
            f"backend/src/routes/auth{ext}",
            f"backend/src/models/User{ext}",
            f"backend/src/services/authService{ext}",
            f"backend/tests/auth.test{ext}",
        ])

    return files


def _go_backend_files(features: List[str]) -> List[str]:
    """Generate Go backend file list."""
    files = [
        "backend/go.mod",
        "backend/go.sum",
        "backend/Dockerfile",
        "backend/.env.example",
        "backend/cmd/server/main.go",
        "backend/internal/config/config.go",
        "backend/internal/handler/health.go",
        "backend/internal/middleware/cors.go",
        "backend/internal/middleware/logger.go",
        "backend/internal/model/user.go",
        "backend/internal/service/auth.go",
        "backend/internal/router/router.go",
        "backend/pkg/utils/helpers.go",
    ]
    return files


def _java_backend_files(features: List[str]) -> List[str]:
    """Generate Java/Spring backend file list."""
    base = "backend/src/main/java/com/app"
    files = [
        "backend/pom.xml",
        "backend/Dockerfile",
        "backend/src/main/resources/application.yml",
        "backend/src/main/resources/application-prod.yml",
        f"{base}/Application.java",
        f"{base}/config/SecurityConfig.java",
        f"{base}/config/WebConfig.java",
        f"{base}/controller/HealthController.java",
        f"{base}/service/UserService.java",
        f"{base}/model/User.java",
        f"{base}/repository/UserRepository.java",
        f"{base}/dto/UserDTO.java",
        f"{base}/exception/GlobalExceptionHandler.java",
    ]
    return files


def _react_frontend_files(features: List[str], styling: str) -> List[str]:
    """Generate React + Vite + TypeScript frontend file list."""
    files = [
        # Config
        "frontend/package.json",
        "frontend/tsconfig.json",
        "frontend/tsconfig.app.json",
        "frontend/tsconfig.node.json",
        "frontend/vite.config.ts",
        "frontend/eslint.config.js",
        "frontend/.prettierrc",
        "frontend/index.html",
    ]

    # Tailwind
    if "tailwind" in styling.lower():
        files.extend([
            "frontend/tailwind.config.ts",
            "frontend/postcss.config.js",
            "frontend/components.json",   # shadcn/ui
        ])

    # Source files
    files.extend([
        "frontend/src/main.tsx",
        "frontend/src/App.tsx",
        "frontend/src/App.css",
        "frontend/src/index.css",
        "frontend/src/vite-env.d.ts",

        # UI Components (shadcn-style)
        "frontend/src/components/ui/button.tsx",
        "frontend/src/components/ui/input.tsx",
        "frontend/src/components/ui/card.tsx",
        "frontend/src/components/ui/dialog.tsx",
        "frontend/src/components/ui/loading-spinner.tsx",
        "frontend/src/components/ui/toast.tsx",

        # Layout
        "frontend/src/components/layout/header.tsx",
        "frontend/src/components/layout/footer.tsx",
        "frontend/src/components/layout/sidebar.tsx",
        "frontend/src/components/layout/root-layout.tsx",

        # Error handling
        "frontend/src/components/error-boundary.tsx",
        "frontend/src/components/not-found.tsx",

        # Lib
        "frontend/src/lib/api-client.ts",
        "frontend/src/lib/utils.ts",
        "frontend/src/lib/constants.ts",
        "frontend/src/lib/validators.ts",

        # Hooks
        "frontend/src/hooks/use-auth.ts",
        "frontend/src/hooks/use-api.ts",
        "frontend/src/hooks/use-debounce.ts",
        "frontend/src/hooks/use-local-storage.ts",

        # Types
        "frontend/src/types/index.ts",
        "frontend/src/types/api.ts",

        # State
        "frontend/src/stores/auth-store.ts",

        # Pages
        "frontend/src/pages/home.tsx",
    ])

    # Feature-specific pages
    feature_lower = " ".join(features).lower()
    if any(f in feature_lower for f in ["auth", "login", "user", "signup", "register"]):
        files.extend([
            "frontend/src/pages/login.tsx",
            "frontend/src/pages/register.tsx",
            "frontend/src/pages/profile.tsx",
            "frontend/src/components/auth/auth-form.tsx",
            "frontend/src/components/auth/protected-route.tsx",
        ])
    if any(f in feature_lower for f in ["dashboard", "admin", "analytics"]):
        files.extend([
            "frontend/src/pages/dashboard.tsx",
            "frontend/src/components/dashboard/stats-card.tsx",
            "frontend/src/components/dashboard/activity-feed.tsx",
            "frontend/src/components/dashboard/chart.tsx",
        ])
    if any(f in feature_lower for f in ["setting", "preference", "config"]):
        files.append("frontend/src/pages/settings.tsx")
    if any(f in feature_lower for f in ["gallery", "image", "media", "photo"]):
        files.extend([
            "frontend/src/pages/gallery.tsx",
            "frontend/src/components/gallery/image-grid.tsx",
            "frontend/src/components/gallery/lightbox.tsx",
        ])

    # Tests
    files.extend([
        "frontend/src/__tests__/App.test.tsx",
        "frontend/vitest.config.ts",
    ])

    return files


def _nextjs_frontend_files(features: List[str], styling: str) -> List[str]:
    """Generate Next.js file list."""
    files = [
        "frontend/package.json",
        "frontend/next.config.ts",
        "frontend/tsconfig.json",
        "frontend/tailwind.config.ts",
        "frontend/postcss.config.js",
        "frontend/eslint.config.js",
        "frontend/components.json",

        # App Router
        "frontend/app/layout.tsx",
        "frontend/app/page.tsx",
        "frontend/app/globals.css",
        "frontend/app/loading.tsx",
        "frontend/app/error.tsx",
        "frontend/app/not-found.tsx",

        # Components
        "frontend/components/ui/button.tsx",
        "frontend/components/ui/input.tsx",
        "frontend/components/ui/card.tsx",
        "frontend/components/layout/header.tsx",
        "frontend/components/layout/footer.tsx",

        # Lib
        "frontend/lib/api-client.ts",
        "frontend/lib/utils.ts",

        # Types
        "frontend/types/index.ts",
    ]
    return files


def _vue_frontend_files(features: List[str], styling: str) -> List[str]:
    """Generate Vue 3 file list."""
    files = [
        "frontend/package.json",
        "frontend/vite.config.ts",
        "frontend/tsconfig.json",
        "frontend/env.d.ts",
        "frontend/index.html",

        "frontend/src/main.ts",
        "frontend/src/App.vue",
        "frontend/src/style.css",
        "frontend/src/router/index.ts",
        "frontend/src/stores/auth.ts",
        "frontend/src/views/HomeView.vue",
        "frontend/src/components/ui/BaseButton.vue",
        "frontend/src/components/ui/BaseInput.vue",
        "frontend/src/components/layout/AppHeader.vue",
        "frontend/src/components/layout/AppFooter.vue",
        "frontend/src/composables/useAuth.ts",
        "frontend/src/lib/api-client.ts",
        "frontend/src/types/index.ts",
    ]
    return files


def _angular_frontend_files(features: List[str]) -> List[str]:
    """Generate Angular file list."""
    files = [
        "frontend/package.json",
        "frontend/angular.json",
        "frontend/tsconfig.json",
        "frontend/tsconfig.app.json",

        "frontend/src/main.ts",
        "frontend/src/index.html",
        "frontend/src/styles.css",
        "frontend/src/app/app.component.ts",
        "frontend/src/app/app.module.ts",
        "frontend/src/app/app-routing.module.ts",
        "frontend/src/app/services/api.service.ts",
        "frontend/src/app/services/auth.service.ts",
        "frontend/src/app/guards/auth.guard.ts",
        "frontend/src/app/components/header/header.component.ts",
        "frontend/src/app/pages/home/home.component.ts",
        "frontend/src/environments/environment.ts",
        "frontend/src/environments/environment.prod.ts",
    ]
    return files


def _svelte_frontend_files(features: List[str], styling: str) -> List[str]:
    """Generate SvelteKit file list."""
    files = [
        "frontend/package.json",
        "frontend/svelte.config.js",
        "frontend/vite.config.ts",
        "frontend/tsconfig.json",

        "frontend/src/app.html",
        "frontend/src/app.css",
        "frontend/src/routes/+layout.svelte",
        "frontend/src/routes/+page.svelte",
        "frontend/src/lib/api-client.ts",
        "frontend/src/lib/utils.ts",
        "frontend/src/lib/components/Header.svelte",
        "frontend/src/lib/components/Footer.svelte",
        "frontend/src/lib/stores/auth.ts",
    ]
    return files


# ═════════════════════════════════════════════════════════════════════════════
# S-CLASS CODE GENERATION GUIDELINES
# ═════════════════════════════════════════════════════════════════════════════

SCLASS_FRONTEND_GUIDELINES = """
S-CLASS FRONTEND CODE STANDARDS:
1. TypeScript ONLY — no .js/.jsx files (use .ts/.tsx)
2. Proper component patterns — FC with typed props interfaces
3. Custom hooks for ALL reusable logic (useAuth, useApi, useDebounce)
4. API client with interceptors, error handling, retry logic, type safety
5. Zustand or TanStack Query for state management — no prop drilling
6. Tailwind CSS with design tokens — no inline styles, no raw CSS in components
7. shadcn/ui-style component library — composable, accessible primitives
8. Error boundaries around every route and async operation
9. Loading skeletons, not spinners — for every async data fetch
10. Form validation with Zod schemas — on both client and server
11. Lazy loading for routes and heavy components
12. Proper SEO — meta tags, OpenGraph, canonical URLs
13. Accessibility — ARIA labels, keyboard navigation, screen reader support
14. Responsive design — mobile-first with breakpoints
15. Environment variables via import.meta.env — never hardcode URLs
16. Consistent naming: PascalCase components, camelCase functions, kebab-case files
17. Every component file < 200 lines — extract sub-components if larger
18. Index files for clean barrel exports
19. Proper error/success toast notifications
20. Protected routes with auth guards
"""

SCLASS_BACKEND_GUIDELINES = """
S-CLASS BACKEND CODE STANDARDS:
1. Full type hints on EVERY function signature and return type
2. Pydantic schemas for ALL request/response bodies — never raw dicts
3. Service layer pattern — controllers are thin, services hold business logic
4. Dependency injection for database sessions, auth, services
5. Proper HTTP status codes — 201 for creation, 204 for deletion, 422 for validation
6. Structured logging with correlation IDs — not print() statements
7. Custom exception classes with proper error responses
8. Rate limiting on auth endpoints and expensive operations
9. Database migrations with Alembic — never raw SQL in code
10. Environment-based configuration — Settings class with validation
11. Health check endpoint with dependency checks (DB, cache, etc.)
12. API versioning — /api/v1/ prefix
13. Pagination for all list endpoints — cursor or offset-based
14. Repository pattern for database queries
15. Background tasks for email, notifications, heavy processing
16. Request validation middleware — reject malformed requests early
17. CORS properly configured — not allow_origins=["*"] in production
18. Password hashing with bcrypt — never store plaintext
19. JWT with proper expiration, refresh tokens, and revocation
20. Comprehensive test suite — unit tests for services, integration tests for API
"""

SCLASS_DEVOPS_GUIDELINES = """
S-CLASS DEVOPS STANDARDS:
1. Multi-stage Docker builds — separate build and runtime stages
2. Docker Compose for local development with hot reload
3. GitHub Actions CI — lint, type-check, test on every PR
4. GitHub Actions CD — deploy on main branch merge
5. Environment-specific configs — .env.example as template
6. Health check endpoints used in Docker HEALTHCHECK
7. Structured logging for container orchestrators
8. Resource limits in Docker Compose
9. Secrets management — never commit .env files
10. Database migration in CI/CD pipeline
"""
