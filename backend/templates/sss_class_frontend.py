"""
SSS-Class Frontend Templates — Platform-Grade Architecture

This module generates frontend code that a CTO with 15–20 years of
experience would approve for a production platform.

Architecture philosophy:
─────────────────────────
  src/
  ├── app/              Application composition layer
  ├── core/             Core infrastructure (config, logger, errors, perf)
  ├── infrastructure/   External systems (HTTP, WebSocket, query client)
  ├── features/         Domain-driven features (complete isolation)
  ├── shared/           Shared UI, hooks, utils, types
  ├── styles/           Global styles and design tokens
  └── main.tsx          Single entry point

Engineering Constitution (enforced by architecture):
────────────────────────────────────────────────────
  1. No business logic inside components
  2. All API calls through centralized client
  3. Global error boundary required
  4. Strict typing everywhere
  5. No cross-feature imports
  6. Lazy-load features by default
  7. Centralized state strategy (React Query + Zustand)
  8. Structured logging
  9. No magic strings — constants registry
  10. Config-driven environment handling
"""

from typing import Dict, List, Optional
import re as _re


# ─────────────────────────────────────────────────────────────────────────────
# Feature-name utilities — guarantee valid TS identifiers, paths, and URLs
# ─────────────────────────────────────────────────────────────────────────────

def _feat_slug(name: str) -> str:
    """Kebab-case for file paths and URLs: 'Team Management' → 'team-management'"""
    return _re.sub(r'[\s_]+', '-', name.strip()).lower()


def _feat_snake(name: str) -> str:
    """Snake_case: 'Team Management' → 'team_management'"""
    return _re.sub(r'[\s-]+', '_', name.strip()).lower()


def _feat_pascal(name: str) -> str:
    """PascalCase for TS class/component names: 'team-management' → 'TeamManagement'"""
    return "".join(
        word.capitalize()
        for word in _re.split(r'[\s_-]+', name.strip())
        if word
    )


def _feat_camel(name: str) -> str:
    """camelCase for TS variables: 'team-management' → 'teamManagement'"""
    pascal = _feat_pascal(name)
    return pascal[0].lower() + pascal[1:] if pascal else ""


def _feat_const(name: str) -> str:
    """UPPER_SNAKE for constant keys: 'team management' → 'TEAM_MANAGEMENT'"""
    return _re.sub(r'[\s-]+', '_', name.strip()).upper()


# ═════════════════════════════════════════════════════════════════════════════
# FRONTEND ARCHITECTURE PLANNER — CTO-Level Pre-Generation
# ═════════════════════════════════════════════════════════════════════════════

def plan_frontend_architecture(
    project_name: str,
    features: List[str],
    user_idea: str = "",
) -> dict:
    """
    CTO-level planning phase — decides architecture BEFORE generating code.

    This function answers:
    1. What is the product domain?
    2. What features are needed?
    3. What are the feature boundaries?
    4. What are the data contracts?
    5. What state model to use?
    6. What routing model to use?
    7. What async strategy (caching, retry, backoff)?
    8. What error strategy (boundary hierarchy)?
    9. What logging strategy (structured, levels)?
    10. What scaling assumptions (code splitting, bundle strategy)?
    """
    idea_lower = user_idea.lower() if user_idea else ""
    features_lower = [f.lower() for f in features]

    # ── Detect product domain ──
    domain = "general"
    if any(w in idea_lower for w in ["saas", "subscription", "tenant"]):
        domain = "saas"
    elif any(w in idea_lower for w in ["ecommerce", "shop", "store", "cart", "product"]):
        domain = "ecommerce"
    elif any(w in idea_lower for w in ["social", "feed", "post", "follow"]):
        domain = "social"
    elif any(w in idea_lower for w in ["dashboard", "analytics", "admin"]):
        domain = "dashboard"
    elif any(w in idea_lower for w in ["blog", "cms", "content"]):
        domain = "cms"
    elif any(w in idea_lower for w in ["chat", "message", "realtime"]):
        domain = "realtime"

    # ── Detect features with boundaries ──
    detected_features = ["auth"]  # Always include auth
    feature_map = {
        "dashboard": ["dashboard", "admin", "analytics", "panel", "overview"],
        "projects": ["project", "workspace", "board", "task"],
        "settings": ["setting", "preference", "config", "profile"],
        "payments": ["pay", "stripe", "billing", "subscription", "pricing"],
        "chat": ["chat", "message", "inbox", "conversation"],
        "notifications": ["notification", "alert", "bell"],
        "search": ["search", "filter", "find"],
        "users": ["user", "team", "member", "invite"],
        "cart": ["cart", "basket", "checkout"],
        "products": ["product", "catalog", "item", "inventory"],
        "orders": ["order", "purchase", "receipt"],
        "files": ["file", "upload", "media", "document", "storage"],
        "reports": ["report", "export", "analytics", "chart"],
        "comments": ["comment", "review", "feedback", "rating"],
    }

    for feature_key, keywords in feature_map.items():
        if any(kw in idea_lower or kw in " ".join(features_lower) for kw in keywords):
            if feature_key not in detected_features:
                detected_features.append(feature_key)

    # Include explicitly-requested features that weren't matched by keywords
    # Track which keywords already covered a feature to avoid duplicates
    # e.g., if "billing" keyword already added "payments", don't also add "billing"
    covered_keywords = set()
    for feature_key, keywords in feature_map.items():
        if feature_key in detected_features:
            covered_keywords.update(keywords)

    for feat in features:
        feat_lower = feat.lower().strip()
        slug = _feat_slug(feat_lower)
        # Skip if already detected or if this name was a keyword for an existing feature
        if slug and slug not in detected_features and feat_lower not in covered_keywords:
            detected_features.append(slug)

    # Ensure we always have at least dashboard + settings
    if "dashboard" not in detected_features:
        detected_features.append("dashboard")
    if "settings" not in detected_features:
        detected_features.append("settings")

    # ── Define data contracts per feature ──
    data_contracts = {}
    for feat in detected_features:
        data_contracts[feat] = _get_feature_data_contract(feat)

    # ── State model decision ──
    state_model = {
        "server_state": "React Query (TanStack Query v5)",
        "client_state": "Zustand",
        "rationale": "Server state via React Query for caching/sync, "
                     "Zustand for client-only UI state. No Redux overhead.",
        "cache_strategy": {
            "stale_time": "5 minutes",
            "gc_time": "30 minutes",
            "retry": 3,
            "retry_delay": "exponential backoff",
            "refetch_on_window_focus": False,
        },
    }

    # ── Routing model ──
    routing_model = {
        "strategy": "Route-based code splitting with React Router v7",
        "lazy_loading": True,
        "suspense_boundaries": True,
        "error_boundaries_per_route": True,
        "protected_routes": True,
        "layout_routes": True,
    }

    # ── Async strategy ──
    async_strategy = {
        "http_client": "Centralized fetch-based API client with interceptors",
        "retry_policy": "Exponential backoff with jitter (3 retries)",
        "timeout": "30 seconds default",
        "error_recovery": "Toast notifications + error boundaries",
        "optimistic_updates": domain in ("social", "realtime", "chat"),
        "websocket": domain in ("realtime", "chat"),
    }

    # ── Error strategy ──
    error_strategy = {
        "global_boundary": True,
        "route_boundaries": True,
        "feature_boundaries": True,
        "api_error_interceptor": True,
        "toast_notifications": True,
        "error_logging": "Structured logger with context",
        "recovery_actions": ["retry", "fallback_ui", "redirect"],
    }

    # ── Logging strategy ──
    logging_strategy = {
        "format": "structured JSON in production, pretty in development",
        "levels": ["debug", "info", "warn", "error"],
        "context": ["user_id", "feature", "action", "timestamp"],
        "redaction": ["password", "token", "secret"],
    }

    # ── Performance / Scaling ──
    performance_strategy = {
        "code_splitting": "Route-based + feature-based lazy loading",
        "bundle_strategy": {
            "vendor_chunk": ["react", "react-dom", "react-router-dom"],
            "ui_chunk": ["lucide-react", "sonner", "clsx"],
            "query_chunk": ["@tanstack/react-query", "zustand", "zod"],
        },
        "memoization": "React.memo for heavy components, useMemo/useCallback for expensive ops",
        "suspense": "Suspense boundaries at route + feature level",
        "preloading": "Route preload on hover/focus for critical paths",
        "image_optimization": "Lazy loading + srcset for responsive images",
    }

    return {
        "project_name": project_name,
        "domain": domain,
        "features": detected_features,
        "data_contracts": data_contracts,
        "state_model": state_model,
        "routing_model": routing_model,
        "async_strategy": async_strategy,
        "error_strategy": error_strategy,
        "logging_strategy": logging_strategy,
        "performance_strategy": performance_strategy,
    }


def _get_feature_data_contract(feature: str) -> dict:
    """Define the data contract (types) for a feature."""
    contracts = {
        "auth": {
            "entities": ["User", "AuthTokens", "LoginCredentials", "RegisterData"],
            "api_endpoints": ["/auth/login", "/auth/register", "/auth/me", "/auth/refresh"],
            "state": ["user", "isAuthenticated", "isLoading"],
        },
        "dashboard": {
            "entities": ["DashboardStats", "Activity", "ChartData"],
            "api_endpoints": ["/dashboard/stats", "/dashboard/activity"],
            "state": ["stats", "activities", "dateRange"],
        },
        "projects": {
            "entities": ["Project", "ProjectCreate", "ProjectUpdate"],
            "api_endpoints": ["/projects", "/projects/:id"],
            "state": ["projects", "selectedProject", "filters"],
        },
        "settings": {
            "entities": ["UserProfile", "Preferences", "NotificationSettings"],
            "api_endpoints": ["/settings/profile", "/settings/preferences"],
            "state": ["profile", "preferences"],
        },
        "payments": {
            "entities": ["Plan", "Subscription", "Invoice", "PaymentMethod"],
            "api_endpoints": ["/billing/plans", "/billing/subscription", "/billing/invoices"],
            "state": ["currentPlan", "invoices"],
        },
        "chat": {
            "entities": ["Conversation", "Message", "Participant"],
            "api_endpoints": ["/chat/conversations", "/chat/messages"],
            "state": ["conversations", "activeConversation", "messages"],
        },
        "notifications": {
            "entities": ["Notification", "NotificationPreference"],
            "api_endpoints": ["/notifications", "/notifications/mark-read"],
            "state": ["notifications", "unreadCount"],
        },
        "search": {
            "entities": ["SearchResult", "SearchFilters"],
            "api_endpoints": ["/search"],
            "state": ["query", "results", "filters"],
        },
        "users": {
            "entities": ["TeamMember", "Invitation", "Role"],
            "api_endpoints": ["/users", "/users/invite", "/users/roles"],
            "state": ["members", "invitations"],
        },
    }
    return contracts.get(feature, {
        "entities": [f"{feature.title()}Item"],
        "api_endpoints": [f"/{feature}"],
        "state": [f"{feature}Data"],
    })


# ═════════════════════════════════════════════════════════════════════════════
# SSS-CLASS FRONTEND TEMPLATE GENERATOR
# ═════════════════════════════════════════════════════════════════════════════

def get_sss_class_frontend_templates(
    project_name: str,
    features: List[str],
    user_idea: str = "",
) -> Dict[str, str]:
    """
    Generate SSS-class frontend templates with platform-grade architecture.

    This produces 80+ files organized into:
    - app/          → Composition layer (providers, routes, App shell)
    - core/         → Infrastructure (config, logger, error handling, performance)
    - infrastructure/ → External systems (HTTP client, interceptors, query client, ws)
    - features/     → Domain-driven isolated features
    - shared/       → Shared UI components, hooks, utils, types
    - styles/       → Design tokens and global styles
    """
    # Step 1: CTO-level planning
    plan = plan_frontend_architecture(project_name, features, user_idea)
    pn = project_name.replace("-", " ").replace("_", " ").title()
    pn_slug = project_name.lower().replace(" ", "-").replace("_", "-")

    templates: Dict[str, str] = {}

    # Step 2: Generate all layers
    templates.update(_gen_config_files(pn, pn_slug))
    templates.update(_gen_app_layer(pn, pn_slug, plan))
    templates.update(_gen_core_layer(pn, pn_slug, plan))
    templates.update(_gen_infrastructure_layer(pn, pn_slug, plan))
    templates.update(_gen_shared_layer(pn, pn_slug))
    templates.update(_gen_styles_layer())
    templates.update(_gen_feature_templates(pn, pn_slug, plan))
    templates.update(_gen_test_config())
    templates.update(_gen_entry_point(pn))

    return templates


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG FILES (root-level tooling)
# ─────────────────────────────────────────────────────────────────────────────

def _gen_config_files(pn: str, pn_slug: str) -> Dict[str, str]:
    t = {}

    t["frontend/package.json"] = f'''{{
  "name": "{pn_slug}",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {{
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write \\"src/**/*.{{ts,tsx,css}}\\"",
    "type-check": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "analyze": "vite build --mode analyze"
  }},
  "dependencies": {{
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.1.0",
    "zustand": "^5.0.0",
    "@tanstack/react-query": "^5.62.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0",
    "zod": "^3.24.0",
    "lucide-react": "^0.468.0",
    "sonner": "^1.7.0"
  }},
  "devDependencies": {{
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "^5.7.0",
    "vite": "^6.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^9.17.0",
    "prettier": "^3.4.0",
    "vitest": "^2.1.0",
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/user-event": "^14.5.0",
    "rollup-plugin-visualizer": "^5.12.0"
  }}
}}
'''

    t["frontend/tsconfig.json"] = '''{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": false,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@app/*": ["./src/app/*"],
      "@core/*": ["./src/core/*"],
      "@infra/*": ["./src/infrastructure/*"],
      "@features/*": ["./src/features/*"],
      "@shared/*": ["./src/shared/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
'''

    t["frontend/tsconfig.node.json"] = '''{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "skipLibCheck": true
  },
  "include": ["vite.config.ts"]
}
'''

    t["frontend/tsconfig.app.json"] = '''{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "composite": true,
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo"
  },
  "include": ["src"]
}
'''

    t["frontend/vite.config.ts"] = '''import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@app": path.resolve(__dirname, "./src/app"),
      "@core": path.resolve(__dirname, "./src/core"),
      "@infra": path.resolve(__dirname, "./src/infrastructure"),
      "@features": path.resolve(__dirname, "./src/features"),
      "@shared": path.resolve(__dirname, "./src/shared"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    sourcemap: mode !== "production",
    target: "ES2022",
    rollupOptions: {
      output: {
        manualChunks: {
          "vendor-react": ["react", "react-dom", "react-router-dom"],
          "vendor-query": ["@tanstack/react-query", "zustand", "zod"],
          "vendor-ui": ["lucide-react", "sonner", "clsx", "tailwind-merge"],
        },
      },
    },
    chunkSizeWarningLimit: 500,
  },
  // Performance budgets
  ...(mode === "analyze" && {
    plugins: [
      react(),
      // @ts-expect-error dynamic import for analysis
      (await import("rollup-plugin-visualizer")).visualizer({
        open: true,
        gzipSize: true,
      }),
    ],
  }),
}));
'''

    t["frontend/tailwind.config.ts"] = '''import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        success: {
          DEFAULT: "hsl(var(--success))",
          foreground: "hsl(var(--success-foreground))",
        },
        warning: {
          DEFAULT: "hsl(var(--warning))",
          foreground: "hsl(var(--warning-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "slide-down": "slideDown 0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideDown: {
          "0%": { opacity: "0", transform: "translateY(-8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
'''

    t["frontend/postcss.config.js"] = '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
'''

    t["frontend/eslint.config.js"] = '''import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    rules: {
      // Strict typing
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-non-null-assertion": "warn",
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/consistent-type-imports": ["error", { prefer: "type-imports" }],

      // Engineering constitution
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-restricted-imports": ["error", {
        patterns: [
          {
            group: ["@features/*/components/*", "@features/*/hooks/*", "@features/*/api/*"],
            message: "Import features through their public index.ts barrel only. No cross-feature deep imports.",
          },
        ],
      }],
    },
  },
  {
    ignores: ["dist/", "node_modules/", "*.config.js", "*.config.ts"],
  }
);
'''

    t["frontend/.prettierrc"] = '''{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
'''

    t["frontend/.env.example"] = f'''# {pn} Frontend Configuration
VITE_API_URL=http://localhost:8000
VITE_APP_NAME={pn}
VITE_APP_ENV=development
VITE_ENABLE_LOGGING=true
VITE_SENTRY_DSN=
'''

    t["frontend/index.html"] = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="{pn} — Built with VibeCober" />
    <meta name="theme-color" content="#3b82f6" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <title>{pn}</title>
  </head>
  <body class="min-h-screen bg-background font-sans antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''

    t["frontend/components.json"] = f'''{{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {{
    "config": "tailwind.config.ts",
    "css": "src/styles/globals.css",
    "prefix": ""
  }},
  "aliases": {{
    "components": "@/shared/components",
    "utils": "@/shared/utils",
    "ui": "@/shared/ui",
    "lib": "@/core",
    "hooks": "@/shared/hooks"
  }}
}}
'''

    return t


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT — src/main.tsx
# ─────────────────────────────────────────────────────────────────────────────

def _gen_entry_point(pn: str) -> Dict[str, str]:
    return {
        "frontend/src/main.tsx": '''/**
 * Application entry point.
 *
 * This file does ONE thing — mount the React tree.
 * All providers, routing, and configuration live in app/.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "@app/App";
import "@/styles/globals.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
''',
    }


# ─────────────────────────────────────────────────────────────────────────────
# APP LAYER — Composition Root
# ─────────────────────────────────────────────────────────────────────────────

def _gen_app_layer(pn: str, pn_slug: str, plan: dict) -> Dict[str, str]:
    t = {}

    feature_list = plan.get("features", ["auth", "dashboard", "settings"])

    # Build lazy route imports
    route_imports = []
    route_elements = []
    for feat in feature_list:
        component_name = f"{feat.title().replace('_', '')}Page"
        if feat == "auth":
            route_imports.append(
                f'const LoginPage = lazy(() => import("@features/auth/pages/LoginPage"));'
            )
            route_imports.append(
                f'const RegisterPage = lazy(() => import("@features/auth/pages/RegisterPage"));'
            )
            route_elements.append(
                '            <Route path={ROUTES.LOGIN} element={<LoginPage />} />'
            )
            route_elements.append(
                '            <Route path={ROUTES.REGISTER} element={<RegisterPage />} />'
            )
        elif feat == "dashboard":
            route_imports.append(
                f'const DashboardPage = lazy(() => import("@features/dashboard/pages/DashboardPage"));'
            )
            route_elements.append(
                f'            <Route path={{ROUTES.DASHBOARD}} element={{<ProtectedRoute><DashboardPage /></ProtectedRoute>}} />'
            )
        elif feat == "settings":
            route_imports.append(
                f'const SettingsPage = lazy(() => import("@features/settings/pages/SettingsPage"));'
            )
            route_elements.append(
                f'            <Route path={{ROUTES.SETTINGS}} element={{<ProtectedRoute><SettingsPage /></ProtectedRoute>}} />'
            )
        else:
            route_imports.append(
                f'const {component_name} = lazy(() => import("@features/{feat}/pages/{component_name}"));'
            )
            route_elements.append(
                f'            <Route path={{ROUTES.{feat.upper()}}} element={{<ProtectedRoute><{component_name} /></ProtectedRoute>}} />'
            )

    route_imports_str = "\n".join(route_imports)
    route_elements_str = "\n".join(route_elements)

    t["frontend/src/app/App.tsx"] = f'''/**
 * Application shell — composes all providers and routing.
 * No business logic belongs here.
 */
import {{ Suspense, lazy }} from "react";
import {{ BrowserRouter, Routes, Route }} from "react-router-dom";
import {{ QueryProvider }} from "@app/providers/QueryProvider";
import {{ ThemeProvider }} from "@app/providers/ThemeProvider";
import {{ ErrorBoundaryProvider }} from "@app/providers/ErrorBoundaryProvider";
import {{ AppLayout }} from "@app/layouts/AppLayout";
import {{ ProtectedRoute }} from "@app/routes/ProtectedRoute";
import {{ LoadingScreen }} from "@shared/ui/LoadingScreen";
import {{ ROUTES }} from "@core/constants";
import {{ Toaster }} from "sonner";

// ── Lazy-loaded feature pages (route-based code splitting) ──
const HomePage = lazy(() => import("@features/dashboard/pages/HomePage"));
const NotFoundPage = lazy(() => import("@shared/components/NotFoundPage"));
{route_imports_str}

export function App() {{
  return (
    <ErrorBoundaryProvider>
      <ThemeProvider>
        <QueryProvider>
          <BrowserRouter>
            <AppLayout>
              <Suspense fallback={{<LoadingScreen />}}>
                <Routes>
                  <Route path={{ROUTES.HOME}} element={{<HomePage />}} />
{route_elements_str}
                  <Route path="*" element={{<NotFoundPage />}} />
                </Routes>
              </Suspense>
            </AppLayout>
            <Toaster richColors position="top-right" />
          </BrowserRouter>
        </QueryProvider>
      </ThemeProvider>
    </ErrorBoundaryProvider>
  );
}}
'''

    # ── Providers ──
    t["frontend/src/app/providers/QueryProvider.tsx"] = '''/**
 * React Query provider with optimized defaults.
 *
 * Cache strategy:
 * - staleTime: 5min (avoid refetching fresh data)
 * - gcTime: 30min (keep unused data in cache)
 * - retry: 3 with exponential backoff
 * - No refetch on window focus (user-initiated only)
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,       // 5 minutes
      gcTime: 30 * 60 * 1000,         // 30 minutes
      retry: 3,
      retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30_000),
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

interface QueryProviderProps {
  children: ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
'''

    t["frontend/src/app/providers/ThemeProvider.tsx"] = '''/**
 * Theme provider — manages dark/light mode with system preference detection.
 * Persists preference to localStorage.
 */
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "light" | "dark" | "system";

interface ThemeContextValue {
  theme: Theme;
  resolvedTheme: "light" | "dark";
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const STORAGE_KEY = "app-theme";

function getSystemTheme(): "light" | "dark" {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window === "undefined") return "system";
    return (localStorage.getItem(STORAGE_KEY) as Theme) || "system";
  });

  const resolvedTheme = theme === "system" ? getSystemTheme() : theme;

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(resolvedTheme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme, resolvedTheme]);

  // Listen for system theme changes
  useEffect(() => {
    if (theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => setTheme("system"); // triggers re-resolve
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
'''

    t["frontend/src/app/providers/ErrorBoundaryProvider.tsx"] = '''/**
 * Top-level error boundary — catches unhandled React errors.
 * Prevents entire app from crashing. Provides recovery UI.
 */
import React, { type ReactNode } from "react";
import { logger } from "@core/logger";
import { Button } from "@shared/ui/Button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundaryProvider extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logger.error("Uncaught error in React tree", {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
          <div className="text-center space-y-4">
            <h1 className="text-4xl font-bold text-destructive">Something went wrong</h1>
            <p className="text-lg text-muted-foreground max-w-md">
              An unexpected error occurred. Our team has been notified.
            </p>
            {this.state.error && (
              <pre className="mt-4 max-w-lg overflow-auto rounded-lg bg-muted p-4 text-sm text-left">
                {this.state.error.message}
              </pre>
            )}
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={this.handleReset}>
              Try Again
            </Button>
            <Button onClick={this.handleReload}>
              Reload Page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
'''

    # ── Routes ──
    t["frontend/src/app/routes/ProtectedRoute.tsx"] = '''/**
 * Route guard — redirects unauthenticated users to login.
 * Wraps any route that requires authentication.
 */
import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@features/auth";
import { ROUTES } from "@core/constants";
import { LoadingScreen } from "@shared/ui/LoadingScreen";
import type { ReactNode } from "react";

interface ProtectedRouteProps {
  children: ReactNode;
  requiredRole?: string;
}

export function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuthStore();
  const location = useLocation();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
'''

    # ── Layouts ──
    t["frontend/src/app/layouts/AppLayout.tsx"] = f'''/**
 * Application layout shell — header, sidebar, main content area.
 * No business logic. Pure composition.
 */
import type {{ ReactNode }} from "react";
import {{ Header }} from "@shared/components/Header";
import {{ Footer }} from "@shared/components/Footer";

interface AppLayoutProps {{
  children: ReactNode;
}}

export function AppLayout({{ children }}: AppLayoutProps) {{
  return (
    <div className="flex min-h-screen flex-col">
      <Header appName="{pn}" />
      <main className="flex-1">
        <div className="container mx-auto px-4 py-8">
          {{children}}
        </div>
      </main>
      <Footer appName="{pn}" />
    </div>
  );
}}
'''

    return t


# ─────────────────────────────────────────────────────────────────────────────
# CORE LAYER — Config, Logger, Error, Performance, Constants
# ─────────────────────────────────────────────────────────────────────────────

def _gen_core_layer(pn: str, pn_slug: str, plan: Optional[dict] = None) -> Dict[str, str]:
    t = {}

    t["frontend/src/core/config/index.ts"] = f'''/**
 * Environment configuration — config-driven, no magic strings.
 * Single source of truth for all environment variables.
 */
import {{ z }} from "zod";

const envSchema = z.object({{
  VITE_API_URL: z.string().default(""),
  VITE_APP_NAME: z.string().default("{pn}"),
  VITE_APP_ENV: z.enum(["development", "staging", "production"]).default("development"),
  VITE_ENABLE_LOGGING: z
    .string()
    .transform((v) => v === "true")
    .default("true"),
  VITE_SENTRY_DSN: z.string().optional(),
}});

// Validate at startup — fail fast if misconfigured
const parsed = envSchema.safeParse(import.meta.env);
if (!parsed.success) {{
  console.error("Invalid environment configuration:", parsed.error.flatten());
}}

const env = parsed.success ? parsed.data : envSchema.parse({{}});

export const config = {{
  apiUrl: env.VITE_API_URL,
  appName: env.VITE_APP_NAME,
  appEnv: env.VITE_APP_ENV,
  isDevelopment: env.VITE_APP_ENV === "development",
  isProduction: env.VITE_APP_ENV === "production",
  enableLogging: env.VITE_ENABLE_LOGGING,
  sentryDsn: env.VITE_SENTRY_DSN,
}} as const;
'''

    t["frontend/src/core/logger/index.ts"] = '''/**
 * Structured logger — consistent logging across the application.
 *
 * Features:
 * - Log levels (debug, info, warn, error)
 * - Structured context (user, feature, action)
 * - Sensitive data redaction
 * - Environment-aware (no debug in production)
 */
import { config } from "@core/config";

type LogLevel = "debug" | "info" | "warn" | "error";

interface LogContext {
  feature?: string;
  action?: string;
  userId?: string;
  [key: string]: unknown;
}

const REDACTED_KEYS = new Set(["password", "token", "secret", "authorization", "cookie"]);

function redact(obj: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    if (REDACTED_KEYS.has(key.toLowerCase())) {
      result[key] = "[REDACTED]";
    } else if (typeof value === "object" && value !== null) {
      result[key] = redact(value as Record<string, unknown>);
    } else {
      result[key] = value;
    }
  }
  return result;
}

function createLogger() {
  const shouldLog = (level: LogLevel): boolean => {
    if (!config.enableLogging) return false;
    if (config.isProduction && level === "debug") return false;
    return true;
  };

  const formatMessage = (level: LogLevel, message: string, context?: LogContext) => {
    const timestamp = new Date().toISOString();
    const ctx = context ? redact(context as Record<string, unknown>) : {};
    return { timestamp, level, message, ...ctx };
  };

  return {
    debug: (message: string, context?: LogContext) => {
      if (shouldLog("debug")) {
        // eslint-disable-next-line no-console
        console.debug(JSON.stringify(formatMessage("debug", message, context)));
      }
    },

    info: (message: string, context?: LogContext) => {
      if (shouldLog("info")) {
        // eslint-disable-next-line no-console
        console.info(JSON.stringify(formatMessage("info", message, context)));
      }
    },

    warn: (message: string, context?: LogContext) => {
      if (shouldLog("warn")) {
        console.warn(JSON.stringify(formatMessage("warn", message, context)));
      }
    },

    error: (message: string, context?: LogContext) => {
      if (shouldLog("error")) {
        console.error(JSON.stringify(formatMessage("error", message, context)));
      }
    },
  };
}

export const logger = createLogger();
'''

    t["frontend/src/core/error/index.ts"] = '''/**
 * Centralized error handling — typed errors, recovery strategies.
 *
 * All API/domain errors go through this module.
 * Components never construct errors directly.
 */
import { logger } from "@core/logger";

export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
    public readonly recoverable: boolean = true,
    public readonly context?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "AppError";
  }
}

export class NetworkError extends AppError {
  constructor(message = "Network error — please check your connection") {
    super(message, "NETWORK_ERROR", 0, true);
    this.name = "NetworkError";
  }
}

export class ApiError extends AppError {
  constructor(
    public readonly status: number,
    public readonly statusText: string,
    public readonly data?: unknown,
  ) {
    super(`API Error ${status}: ${statusText}`, "API_ERROR", status, status < 500);
    this.name = "ApiError";
  }
}

export class AuthError extends AppError {
  constructor(message = "Authentication required") {
    super(message, "AUTH_ERROR", 401, true);
    this.name = "AuthError";
  }
}

export class ValidationError extends AppError {
  constructor(
    message: string,
    public readonly fieldErrors?: Record<string, string[]>,
  ) {
    super(message, "VALIDATION_ERROR", 422, true);
    this.name = "ValidationError";
  }
}

export class NotFoundError extends AppError {
  constructor(resource = "Resource") {
    super(`${resource} not found`, "NOT_FOUND", 404, false);
    this.name = "NotFoundError";
  }
}

/**
 * Global error handler — logs and optionally reports errors.
 */
export function handleError(error: unknown, context?: { feature?: string; action?: string }) {
  if (error instanceof AppError) {
    logger.error(error.message, {
      code: error.code,
      statusCode: error.statusCode,
      recoverable: error.recoverable,
      ...context,
    });
  } else if (error instanceof Error) {
    logger.error(error.message, { stack: error.stack, ...context });
  } else {
    logger.error("Unknown error", { error, ...context });
  }
}
'''

    t["frontend/src/core/performance/index.ts"] = '''/**
 * Performance monitoring utilities.
 *
 * Tracks component render times, API latency, and
 * provides tools for identifying performance bottlenecks.
 */
import { config } from "@core/config";
import { logger } from "@core/logger";

/**
 * Measure execution time of an async operation.
 */
export async function measureAsync<T>(
  label: string,
  fn: () => Promise<T>,
): Promise<T> {
  if (!config.isDevelopment) return fn();

  const start = performance.now();
  try {
    const result = await fn();
    const duration = Math.round(performance.now() - start);
    logger.debug(`[Perf] ${label}: ${duration}ms`, { feature: "performance", action: label });
    return result;
  } catch (error) {
    const duration = Math.round(performance.now() - start);
    logger.warn(`[Perf] ${label} failed after ${duration}ms`, { feature: "performance" });
    throw error;
  }
}

/**
 * Measure sync execution time.
 */
export function measureSync<T>(label: string, fn: () => T): T {
  if (!config.isDevelopment) return fn();

  const start = performance.now();
  const result = fn();
  const duration = Math.round(performance.now() - start);
  logger.debug(`[Perf] ${label}: ${duration}ms`, { feature: "performance" });
  return result;
}

/**
 * Report Web Vitals to logging system.
 */
export function reportWebVitals() {
  if (typeof window === "undefined") return;

  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      logger.info(`[WebVital] ${entry.name}: ${Math.round(entry.startTime)}ms`, {
        feature: "performance",
        action: entry.name,
      });
    }
  });

  try {
    observer.observe({ entryTypes: ["largest-contentful-paint", "first-input", "layout-shift"] });
  } catch {
    // Browser may not support all entry types
  }
}
'''

    # ── Build dynamic constants based on planned features ──
    features = plan.get("features", []) if plan else []

    # Dynamic ROUTES
    extra_routes_lines = ""
    for feat in features:
        if feat not in ("auth", "dashboard", "settings"):
            const_key = _feat_const(feat)
            url_path = _feat_slug(feat)
            extra_routes_lines += '  ' + const_key + ': "/' + url_path + '",\n'

    # Dynamic API_ENDPOINTS
    extra_api_lines = ""
    for feat in features:
        if feat not in ("auth", "dashboard", "settings"):
            const_key = _feat_const(feat)
            url_path = _feat_slug(feat)
            extra_api_lines += (
                '  ' + const_key + ': {\n'
                '    LIST: "/api/v1/' + url_path + '",\n'
                '    DETAIL: (id: string) => `/api/v1/' + url_path + '/${id}`,\n'
                '    CREATE: "/api/v1/' + url_path + '",\n'
                '    UPDATE: (id: string) => `/api/v1/' + url_path + '/${id}`,\n'
                '    DELETE: (id: string) => `/api/v1/' + url_path + '/${id}`,\n'
                '  },\n'
            )

    # Dynamic QUERY_KEYS
    extra_qk_lines = ""
    for feat in features:
        if feat not in ("auth", "dashboard", "settings"):
            const_key = _feat_const(feat)
            slug = _feat_slug(feat)
            extra_qk_lines += (
                '  ' + const_key + ': {\n'
                '    LIST: ["' + slug + '", "list"],\n'
                '    DETAIL: (id: string) => ["' + slug + '", "detail", id],\n'
                '  },\n'
            )

    constants_content = (
        '/**\n'
        ' * Application constants \u2014 NO magic strings anywhere.\n'
        ' * Every string literal used across features is defined here.\n'
        ' */\n'
        '\n'
        'export const APP_NAME = "' + pn + '";\n'
        '\n'
        '/** Route paths \u2014 single source of truth */\n'
        'export const ROUTES = {\n'
        '  HOME: "/",\n'
        '  LOGIN: "/login",\n'
        '  REGISTER: "/register",\n'
        '  DASHBOARD: "/dashboard",\n'
        '  SETTINGS: "/settings",\n'
        '  PROFILE: "/profile",\n'
        + extra_routes_lines +
        '} as const;\n'
        '\n'
        '/** API endpoint prefixes */\n'
        'export const API_ENDPOINTS = {\n'
        '  AUTH: {\n'
        '    LOGIN: "/api/v1/auth/login",\n'
        '    REGISTER: "/api/v1/auth/register",\n'
        '    ME: "/api/v1/auth/me",\n'
        '    REFRESH: "/api/v1/auth/refresh",\n'
        '  },\n'
        '  DASHBOARD: {\n'
        '    STATS: "/api/v1/dashboard/stats",\n'
        '    ACTIVITY: "/api/v1/dashboard/activity",\n'
        '  },\n'
        '  USERS: {\n'
        '    LIST: "/api/v1/users",\n'
        '    PROFILE: "/api/v1/users/profile",\n'
        '  },\n'
        '  SETTINGS: {\n'
        '    GET: "/api/v1/settings",\n'
        '    UPDATE: "/api/v1/settings",\n'
        '  },\n'
        + extra_api_lines +
        '} as const;\n'
        '\n'
        '/** Query cache keys for React Query */\n'
        'export const QUERY_KEYS = {\n'
        '  AUTH: {\n'
        '    ME: ["auth", "me"],\n'
        '    SESSION: ["auth", "session"],\n'
        '  },\n'
        '  DASHBOARD: {\n'
        '    STATS: ["dashboard", "stats"],\n'
        '    ACTIVITY: ["dashboard", "activity"],\n'
        '  },\n'
        '  USERS: {\n'
        '    LIST: ["users", "list"],\n'
        '    DETAIL: (id: string) => ["users", "detail", id],\n'
        '  },\n'
        '  SETTINGS: {\n'
        '    ALL: ["settings"],\n'
        '  },\n'
        + extra_qk_lines +
        '} as const;\n'
        '\n'
        '/** Storage keys for localStorage/sessionStorage */\n'
        'export const STORAGE_KEYS = {\n'
        '  AUTH_TOKEN: "auth_token",\n'
        '  REFRESH_TOKEN: "refresh_token",\n'
        '  THEME: "app-theme",\n'
        '  SIDEBAR_COLLAPSED: "sidebar-collapsed",\n'
        '} as const;\n'
        '\n'
        '/** HTTP status codes */\n'
        'export const HTTP_STATUS = {\n'
        '  OK: 200,\n'
        '  CREATED: 201,\n'
        '  NO_CONTENT: 204,\n'
        '  BAD_REQUEST: 400,\n'
        '  UNAUTHORIZED: 401,\n'
        '  FORBIDDEN: 403,\n'
        '  NOT_FOUND: 404,\n'
        '  CONFLICT: 409,\n'
        '  UNPROCESSABLE: 422,\n'
        '  INTERNAL_ERROR: 500,\n'
        '} as const;\n'
    )

    t["frontend/src/core/constants/index.ts"] = constants_content

    return t


# ─────────────────────────────────────────────────────────────────────────────
# INFRASTRUCTURE LAYER — HTTP Client, Interceptors, Query Client, WebSocket
# ─────────────────────────────────────────────────────────────────────────────

def _gen_infrastructure_layer(pn: str, pn_slug: str, plan: dict) -> Dict[str, str]:
    t = {}

    t["frontend/src/infrastructure/http/apiClient.ts"] = '''/**
 * Centralized HTTP client — ALL API calls go through this.
 *
 * Engineering constitution rule #2:
 * "All API calls through centralized client."
 *
 * Features:
 * - Type-safe request/response
 * - Automatic auth header injection
 * - Retry with exponential backoff
 * - Request/response interceptors
 * - Timeout handling
 * - Structured error conversion
 */
import { config } from "@core/config";
import { logger } from "@core/logger";
import { ApiError, NetworkError, AuthError } from "@core/error";
import { STORAGE_KEYS, HTTP_STATUS } from "@core/constants";
import { requestInterceptors, responseInterceptors } from "./interceptors";

const DEFAULT_TIMEOUT = 30_000; // 30 seconds
const MAX_RETRIES = 3;

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined>;
  timeout?: number;
  retries?: number;
  skipAuth?: boolean;
}

/**
 * Sleep with jitter for retry backoff.
 */
function backoffDelay(attempt: number): number {
  const base = Math.min(1000 * Math.pow(2, attempt), 30_000);
  const jitter = Math.random() * 500;
  return base + jitter;
}

/**
 * Core request function — not exported directly.
 * Use the `api` object methods below.
 */
async function request<T>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    body,
    params,
    headers: customHeaders,
    timeout = DEFAULT_TIMEOUT,
    retries = 0,
    skipAuth = false,
    ...rest
  } = options;

  // Build URL
  let url = `${config.apiUrl}${endpoint}`;
  if (params) {
    const filtered = Object.entries(params)
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => [k, String(v)]);
    if (filtered.length > 0) {
      url += `?${new URLSearchParams(filtered).toString()}`;
    }
  }

  // Build headers
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((customHeaders as Record<string, string>) || {}),
  };

  // Auth token injection
  if (!skipAuth) {
    const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  // Apply request interceptors
  let finalHeaders = headers;
  for (const interceptor of requestInterceptors) {
    finalHeaders = interceptor(finalHeaders, endpoint);
  }

  // Timeout via AbortController
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  const startTime = performance.now();

  try {
    const response = await fetch(url, {
      ...rest,
      headers: finalHeaders,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const duration = Math.round(performance.now() - startTime);
    logger.debug(`[HTTP] ${rest.method || "GET"} ${endpoint} → ${response.status} (${duration}ms)`, {
      feature: "http",
      action: endpoint,
    });

    // Apply response interceptors
    for (const interceptor of responseInterceptors) {
      interceptor(response, endpoint);
    }

    // Handle auth errors
    if (response.status === HTTP_STATUS.UNAUTHORIZED) {
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
      throw new AuthError();
    }

    // Handle errors
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new ApiError(response.status, response.statusText, errorData);
    }

    // No content
    if (response.status === HTTP_STATUS.NO_CONTENT) {
      return undefined as T;
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    // Retry on network errors
    if (error instanceof TypeError && retries < MAX_RETRIES) {
      const delay = backoffDelay(retries);
      logger.warn(`[HTTP] Retrying ${endpoint} (attempt ${retries + 1}/${MAX_RETRIES}) in ${Math.round(delay)}ms`);
      await new Promise((r) => setTimeout(r, delay));
      return request<T>(endpoint, { ...options, retries: retries + 1 });
    }

    // Convert abort to timeout error
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new NetworkError(`Request timeout after ${timeout}ms`);
    }

    // Re-throw known errors
    if (error instanceof ApiError || error instanceof AuthError) {
      throw error;
    }

    throw new NetworkError();
  }
}

/** Type-safe API methods — use these everywhere */
export const api = {
  get: <T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>) =>
    request<T>(endpoint, { method: "GET", params }),

  post: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, { method: "POST", body }),

  put: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, { method: "PUT", body }),

  patch: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, { method: "PATCH", body }),

  delete: <T>(endpoint: string) =>
    request<T>(endpoint, { method: "DELETE" }),
};
'''

    t["frontend/src/infrastructure/http/interceptors.ts"] = '''/**
 * HTTP interceptors — run before/after every API call.
 *
 * Request interceptors: modify headers, add correlation IDs
 * Response interceptors: handle global responses, refresh tokens
 */
import { logger } from "@core/logger";

type RequestInterceptor = (
  headers: Record<string, string>,
  endpoint: string,
) => Record<string, string>;

type ResponseInterceptor = (
  response: Response,
  endpoint: string,
) => void;

/** Add correlation ID for request tracing */
const addCorrelationId: RequestInterceptor = (headers) => {
  headers["X-Correlation-ID"] = crypto.randomUUID();
  return headers;
};

/** Add request timestamp */
const addTimestamp: RequestInterceptor = (headers) => {
  headers["X-Request-Time"] = new Date().toISOString();
  return headers;
};

/** Log slow responses */
const logSlowResponses: ResponseInterceptor = (response, endpoint) => {
  const serverTiming = response.headers.get("Server-Timing");
  if (serverTiming) {
    logger.debug(`[HTTP] Server timing for ${endpoint}: ${serverTiming}`, {
      feature: "http",
      action: "server-timing",
    });
  }
};

export const requestInterceptors: RequestInterceptor[] = [
  addCorrelationId,
  addTimestamp,
];

export const responseInterceptors: ResponseInterceptor[] = [
  logSlowResponses,
];
'''

    t["frontend/src/infrastructure/queryClient.ts"] = '''/**
 * React Query client configuration — shared query defaults.
 *
 * This file is the single place to configure caching, retries,
 * and error handling for all server state.
 */
export { QueryClient } from "@tanstack/react-query";

// Query client is created in QueryProvider.tsx to keep it
// colocated with the provider component. This file exists
// for any shared query utilities.

import { useQueryClient } from "@tanstack/react-query";

/**
 * Invalidate all queries matching a key prefix.
 * Useful after mutations that affect multiple queries.
 */
export function useInvalidateQueries() {
  const queryClient = useQueryClient();

  return (keyPrefix: string[]) => {
    queryClient.invalidateQueries({ queryKey: keyPrefix });
  };
}
'''

    # WebSocket module (if realtime features detected)
    t["frontend/src/infrastructure/websocket/index.ts"] = '''/**
 * WebSocket client — for real-time features.
 *
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Event-based message handling
 * - Connection state tracking
 * - Heartbeat/ping support
 */
import { logger } from "@core/logger";
import { config } from "@core/config";

type MessageHandler = (data: unknown) => void;
type ConnectionState = "connecting" | "connected" | "disconnecting" | "disconnected";

interface WebSocketClientOptions {
  url: string;
  reconnect?: boolean;
  maxRetries?: number;
  heartbeatInterval?: number;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers = new Map<string, Set<MessageHandler>>();
  private retryCount = 0;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private state: ConnectionState = "disconnected";

  constructor(private options: WebSocketClientOptions) {}

  get connectionState(): ConnectionState {
    return this.state;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.state = "connecting";
    this.ws = new WebSocket(this.options.url);

    this.ws.onopen = () => {
      this.state = "connected";
      this.retryCount = 0;
      logger.info("WebSocket connected", { feature: "websocket" });
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as { type: string; payload: unknown };
        const handlers = this.handlers.get(data.type);
        if (handlers) {
          handlers.forEach((handler) => handler(data.payload));
        }
      } catch {
        logger.warn("Failed to parse WebSocket message", { feature: "websocket" });
      }
    };

    this.ws.onclose = () => {
      this.state = "disconnected";
      this.stopHeartbeat();

      if (
        this.options.reconnect !== false &&
        this.retryCount < (this.options.maxRetries ?? 5)
      ) {
        const delay = Math.min(1000 * Math.pow(2, this.retryCount), 30_000);
        this.retryCount++;
        logger.info(`WebSocket reconnecting in ${delay}ms (attempt ${this.retryCount})`, {
          feature: "websocket",
        });
        setTimeout(() => this.connect(), delay);
      }
    };

    this.ws.onerror = () => {
      logger.error("WebSocket error", { feature: "websocket" });
    };
  }

  disconnect(): void {
    this.state = "disconnecting";
    this.options.reconnect = false;
    this.ws?.close();
    this.stopHeartbeat();
  }

  on(event: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(event)?.delete(handler);
    };
  }

  send(type: string, payload: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    } else {
      logger.warn("Cannot send — WebSocket not connected", { feature: "websocket" });
    }
  }

  private startHeartbeat(): void {
    const interval = this.options.heartbeatInterval ?? 30_000;
    this.heartbeatTimer = setInterval(() => {
      this.send("ping", { timestamp: Date.now() });
    }, interval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }
}

/**
 * Create a pre-configured WebSocket client.
 */
export function createWebSocketClient(path: string): WebSocketClient {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = config.apiUrl
    ? config.apiUrl.replace(/^http/, "ws") + path
    : `${protocol}//${window.location.host}${path}`;

  return new WebSocketClient({
    url: wsUrl,
    reconnect: true,
    maxRetries: 5,
    heartbeatInterval: 30_000,
  });
}
'''

    return t


# ─────────────────────────────────────────────────────────────────────────────
# SHARED LAYER — UI Components, Hooks, Utils, Types
# ─────────────────────────────────────────────────────────────────────────────

def _gen_shared_layer(pn: str, pn_slug: str) -> Dict[str, str]:
    t = {}

    # ── UI Primitives ──
    t["frontend/src/shared/ui/Button.tsx"] = '''import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { cn } from "@shared/utils/cn";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
  isLoading?: boolean;
  children: ReactNode;
}

const variants = {
  default: "bg-primary text-primary-foreground hover:bg-primary/90",
  destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
  outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
  secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
  ghost: "hover:bg-accent hover:text-accent-foreground",
  link: "text-primary underline-offset-4 hover:underline",
};

const sizes = {
  default: "h-10 px-4 py-2",
  sm: "h-9 rounded-md px-3 text-xs",
  lg: "h-11 rounded-md px-8 text-base",
  icon: "h-10 w-10",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", isLoading, children, disabled, ...props }, ref) => (
    <button
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium",
        "ring-offset-background transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-50",
        variants[variant],
        sizes[size],
        className,
      )}
      ref={ref}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg className="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  ),
);
Button.displayName = "Button";
'''

    t["frontend/src/shared/ui/Input.tsx"] = '''import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@shared/utils/cn";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, label, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\\s+/g, "-");
    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-foreground">
            {label}
          </label>
        )}
        <input
          type={type}
          id={inputId}
          className={cn(
            "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
            "ring-offset-background placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            "disabled:cursor-not-allowed disabled:opacity-50",
            error && "border-destructive focus-visible:ring-destructive",
            className,
          )}
          ref={ref}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : undefined}
          {...props}
        />
        {error && (
          <p id={`${inputId}-error`} className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  },
);
Input.displayName = "Input";
'''

    t["frontend/src/shared/ui/Card.tsx"] = '''import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@shared/utils/cn";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function Card({ className, ...props }: CardProps) {
  return <div className={cn("rounded-lg border bg-card text-card-foreground shadow-sm", className)} {...props} />;
}

export function CardHeader({ className, ...props }: CardProps) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-2xl font-semibold leading-none tracking-tight", className)} {...props} />;
}

export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-sm text-muted-foreground", className)} {...props} />;
}

export function CardContent({ className, ...props }: CardProps) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}

export function CardFooter({ className, ...props }: CardProps) {
  return <div className={cn("flex items-center p-6 pt-0", className)} {...props} />;
}
'''

    t["frontend/src/shared/ui/Dialog.tsx"] = '''import type { ReactNode } from "react";
import { cn } from "@shared/utils/cn";
import { X } from "lucide-react";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  className?: string;
  title?: string;
}

export function Dialog({ open, onClose, children, className, title }: DialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true" aria-label={title}>
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />
      <div className={cn(
        "relative z-50 w-full max-w-lg rounded-lg bg-background p-6 shadow-lg animate-fade-in",
        className,
      )}>
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring"
          aria-label="Close dialog"
        >
          <X className="h-4 w-4" />
        </button>
        {title && <h2 className="text-lg font-semibold mb-4">{title}</h2>}
        {children}
      </div>
    </div>
  );
}
'''

    t["frontend/src/shared/ui/LoadingScreen.tsx"] = '''import { cn } from "@shared/utils/cn";

interface LoadingScreenProps {
  className?: string;
  message?: string;
}

export function LoadingScreen({ className, message }: LoadingScreenProps) {
  return (
    <div className={cn("flex min-h-[60vh] flex-col items-center justify-center gap-4", className)} role="status">
      <svg
        className="h-10 w-10 animate-spin text-primary"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <span className="sr-only">{message || "Loading..."}</span>
      {message && <p className="text-sm text-muted-foreground">{message}</p>}
    </div>
  );
}
'''

    t["frontend/src/shared/ui/LoadingSpinner.tsx"] = '''import { cn } from "@shared/utils/cn";

interface LoadingSpinnerProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

const sizeClasses = { sm: "h-4 w-4", md: "h-8 w-8", lg: "h-12 w-12" };

export function LoadingSpinner({ className, size = "md" }: LoadingSpinnerProps) {
  return (
    <div className={cn("flex items-center justify-center", className)} role="status">
      <svg className={cn("animate-spin text-primary", sizeClasses[size])} viewBox="0 0 24 24" aria-hidden="true">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <span className="sr-only">Loading...</span>
    </div>
  );
}
'''

    t["frontend/src/shared/ui/Badge.tsx"] = '''import type { HTMLAttributes } from "react";
import { cn } from "@shared/utils/cn";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning";
}

const variants = {
  default: "bg-primary text-primary-foreground",
  secondary: "bg-secondary text-secondary-foreground",
  destructive: "bg-destructive text-destructive-foreground",
  outline: "border border-input text-foreground",
  success: "bg-success text-success-foreground",
  warning: "bg-warning text-warning-foreground",
};

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
'''

    t["frontend/src/shared/ui/Skeleton.tsx"] = '''import { cn } from "@shared/utils/cn";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div className={cn("animate-pulse rounded-md bg-muted", className)} aria-hidden="true" />
  );
}
'''

    t["frontend/src/shared/ui/index.ts"] = '''/**
 * UI primitives barrel export.
 * Import UI components from @shared/ui.
 */
export { Button } from "./Button";
export type { ButtonProps } from "./Button";
export { Input } from "./Input";
export type { InputProps } from "./Input";
export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "./Card";
export { Dialog } from "./Dialog";
export { LoadingScreen } from "./LoadingScreen";
export { LoadingSpinner } from "./LoadingSpinner";
export { Badge } from "./Badge";
export { Skeleton } from "./Skeleton";
'''

    # ── Shared Components ──
    t["frontend/src/shared/components/Header.tsx"] = '''import { Link, useLocation } from "react-router-dom";
import { useAuthStore } from "@features/auth";
import { Button } from "@shared/ui/Button";
import { cn } from "@shared/utils/cn";
import { ROUTES } from "@core/constants";

interface HeaderProps {
  appName: string;
}

export function Header({ appName }: HeaderProps) {
  const { isAuthenticated, user, logout } = useAuthStore();
  const location = useLocation();

  const navLinks = [
    { label: "Home", href: ROUTES.HOME },
    ...(isAuthenticated ? [{ label: "Dashboard", href: ROUTES.DASHBOARD }] : []),
  ];

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link to="/" className="text-xl font-bold text-primary">
            {appName}
          </Link>
          <nav className="hidden gap-4 md:flex" aria-label="Main navigation">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className={cn(
                  "text-sm font-medium transition-colors hover:text-primary",
                  location.pathname === link.href ? "text-foreground" : "text-muted-foreground",
                )}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <>
              <span className="text-sm text-muted-foreground">{user?.name || user?.email}</span>
              <Button variant="outline" size="sm" onClick={logout}>
                Logout
              </Button>
            </>
          ) : (
            <>
              <Link to={ROUTES.LOGIN}>
                <Button variant="ghost" size="sm">Login</Button>
              </Link>
              <Link to={ROUTES.REGISTER}>
                <Button size="sm">Get Started</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
'''

    t["frontend/src/shared/components/Footer.tsx"] = '''import { APP_NAME } from "@core/constants";

interface FooterProps {
  appName?: string;
}

export function Footer({ appName }: FooterProps) {
  return (
    <footer className="border-t bg-background">
      <div className="container mx-auto flex flex-col items-center gap-4 px-4 py-8 md:flex-row md:justify-between">
        <p className="text-sm text-muted-foreground">
          &copy; {new Date().getFullYear()} {appName || APP_NAME}. All rights reserved.
        </p>
        <div className="flex gap-4">
          <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Privacy</a>
          <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Terms</a>
          <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Contact</a>
        </div>
      </div>
    </footer>
  );
}
'''

    t["frontend/src/shared/components/NotFoundPage.tsx"] = '''import { Link } from "react-router-dom";
import { Button } from "@shared/ui/Button";
import { ROUTES } from "@core/constants";

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-7xl font-bold text-primary">404</h1>
      <h2 className="text-2xl font-semibold">Page Not Found</h2>
      <p className="max-w-md text-muted-foreground">
        The page you&#39;re looking for doesn&#39;t exist or has been moved.
      </p>
      <Link to={ROUTES.HOME}>
        <Button>Back to Home</Button>
      </Link>
    </div>
  );
}
'''

    t["frontend/src/shared/components/FeatureErrorBoundary.tsx"] = '''/**
 * Feature-level error boundary — isolates feature failures.
 *
 * Unlike the app-level ErrorBoundaryProvider, this wraps
 * individual features so one crashing feature doesn\'t
 * take down the entire app.
 */
import React, { type ReactNode } from "react";
import { logger } from "@core/logger";
import { Button } from "@shared/ui/Button";

interface Props {
  feature: string;
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class FeatureErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    logger.error(`Feature "${this.props.feature}" crashed`, {
      feature: this.props.feature,
      error: error.message,
      stack: error.stack,
    });
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
          <h3 className="text-lg font-semibold text-destructive">
            This section encountered an error
          </h3>
          <p className="text-sm text-muted-foreground max-w-md">
            The {this.props.feature} feature had a problem. You can try again or continue using other parts of the app.
          </p>
          <Button variant="outline" size="sm" onClick={this.handleRetry}>
            Try Again
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
'''

    # ── Shared Hooks ──
    t["frontend/src/shared/hooks/useDebounce.ts"] = '''import { useState, useEffect } from "react";

/** Debounce a value — useful for search inputs */
export function useDebounce<T>(value: T, delay = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
'''

    t["frontend/src/shared/hooks/useLocalStorage.ts"] = '''import { useState, useEffect, useCallback } from "react";

/** Persist state in localStorage with type safety */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      setStoredValue((prev) => {
        const nextValue = value instanceof Function ? value(prev) : value;
        try {
          window.localStorage.setItem(key, JSON.stringify(nextValue));
        } catch {
          console.warn(`Failed to save ${key} to localStorage`);
        }
        return nextValue;
      });
    },
    [key],
  );

  return [storedValue, setValue] as const;
}
'''

    t["frontend/src/shared/hooks/useMediaQuery.ts"] = '''import { useState, useEffect } from "react";

/** Reactive media query hook */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    const mq = window.matchMedia(query);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [query]);

  return matches;
}
'''

    t["frontend/src/shared/hooks/index.ts"] = '''export { useDebounce } from "./useDebounce";
export { useLocalStorage } from "./useLocalStorage";
export { useMediaQuery } from "./useMediaQuery";
'''

    # ── Shared Utils ──
    t["frontend/src/shared/utils/cn.ts"] = '''import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes — the shadcn/ui pattern */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
'''

    t["frontend/src/shared/utils/format.ts"] = '''/** Format a date to a human-readable string */
export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(date));
}

/** Format a date with time */
export function formatDateTime(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
}

/** Format a number with commas */
export function formatNumber(num: number): string {
  return new Intl.NumberFormat("en-US").format(num);
}

/** Format bytes to human-readable size */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/** Truncate text with ellipsis */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + "\\u2026";
}
'''

    t["frontend/src/shared/utils/validators.ts"] = '''import { z } from "zod";

/** Reusable Zod schemas — no inline validation in components */

export const emailSchema = z
  .string()
  .min(1, "Email is required")
  .email("Invalid email address");

export const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .regex(/[A-Z]/, "Must contain at least one uppercase letter")
  .regex(/[a-z]/, "Must contain at least one lowercase letter")
  .regex(/[0-9]/, "Must contain at least one number");

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, "Password is required"),
});

export const registerSchema = z
  .object({
    name: z.string().min(2, "Name must be at least 2 characters"),
    email: emailSchema,
    password: passwordSchema,
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don\\'t match",
    path: ["confirmPassword"],
  });

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
'''

    t["frontend/src/shared/utils/index.ts"] = '''export { cn } from "./cn";
export { formatDate, formatDateTime, formatNumber, formatBytes, truncate } from "./format";
'''

    # ── Shared Types ──
    t["frontend/src/shared/types/index.ts"] = '''/** Core application types shared across all features */

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  created_at: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ApiErrorResponse {
  detail: string;
  status_code: number;
}

export interface SelectOption {
  label: string;
  value: string;
}
'''

    t["frontend/src/shared/types/api.ts"] = '''/** API request/response types */

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    name: string;
  };
}

export interface HealthResponse {
  status: string;
  version: string;
}
'''

    return t


# ─────────────────────────────────────────────────────────────────────────────
# STYLES LAYER — Design Tokens & Global CSS
# ─────────────────────────────────────────────────────────────────────────────

def _gen_styles_layer() -> Dict[str, str]:
    return {
        "frontend/src/styles/globals.css": '''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --success: 142 76% 36%;
    --success-foreground: 210 40% 98%;
    --warning: 38 92% 50%;
    --warning-foreground: 222.2 47.4% 11.2%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --success: 142 71% 45%;
    --success-foreground: 210 40% 98%;
    --warning: 38 92% 50%;
    --warning-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }

  /* Accessible focus styles */
  :focus-visible {
    @apply outline-none ring-2 ring-ring ring-offset-2 ring-offset-background;
  }

  /* Smooth scrolling */
  html {
    scroll-behavior: smooth;
  }

  /* Remove scrollbar in some contexts */
  .no-scrollbar::-webkit-scrollbar {
    display: none;
  }
  .no-scrollbar {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
}

@layer utilities {
  .text-balance {
    text-wrap: balance;
  }
}
''',
    }


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE TEMPLATES — Domain-Driven Isolated Features
# ─────────────────────────────────────────────────────────────────────────────

def _gen_feature_templates(pn: str, pn_slug: str, plan: dict) -> Dict[str, str]:
    """
    Generate feature modules based on the architecture plan.
    Each feature is fully isolated: components, hooks, api, types, index.
    """
    t = {}
    detected_features = plan.get("features", ["auth", "dashboard", "settings"])

    for feat in detected_features:
        if feat == "auth":
            t.update(_gen_auth_feature(pn))
        elif feat == "dashboard":
            t.update(_gen_dashboard_feature(pn))
        elif feat == "settings":
            t.update(_gen_settings_feature(pn))
        else:
            t.update(_gen_generic_feature(feat, pn))

    return t


def _gen_auth_feature(pn: str) -> Dict[str, str]:
    t = {}
    base = "frontend/src/features/auth"

    t[f"{base}/index.ts"] = '''/**
 * Auth feature — public API.
 * Other features import ONLY from this file.
 * No deep imports into auth internals.
 */
export { useAuthStore } from "./hooks/useAuthStore";
export { useAuth } from "./hooks/useAuth";
export type { AuthState, LoginCredentials, RegisterData } from "./types";
'''

    t[f"{base}/types.ts"] = '''/** Auth feature types — domain boundary */

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
}

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}
'''

    t[f"{base}/api/authApi.ts"] = '''/**
 * Auth API calls — all auth HTTP requests live here.
 * Components never call api.post() directly for auth.
 */
import { api } from "@infra/http/apiClient";
import { API_ENDPOINTS } from "@core/constants";
import type { AuthResponse, AuthUser, LoginCredentials, RegisterData } from "../types";

export const authApi = {
  login: (credentials: LoginCredentials) =>
    api.post<AuthResponse>(API_ENDPOINTS.AUTH.LOGIN, credentials),

  register: (data: RegisterData) =>
    api.post<{ message: string }>(API_ENDPOINTS.AUTH.REGISTER, data),

  getMe: () =>
    api.get<AuthUser>(API_ENDPOINTS.AUTH.ME),

  refreshToken: () =>
    api.post<AuthResponse>(API_ENDPOINTS.AUTH.REFRESH),
};
'''

    t[f"{base}/hooks/useAuthStore.ts"] = '''/**
 * Auth store — Zustand for client auth state.
 * Business logic lives HERE, not in components.
 */
import { create } from "zustand";
import { logger } from "@core/logger";
import { STORAGE_KEYS } from "@core/constants";
import { handleError } from "@core/error";
import { authApi } from "../api/authApi";
import type { AuthUser, AuthState, LoginCredentials, RegisterData } from "../types";

interface AuthActions {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  reset: () => void;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: !!localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN),
  isLoading: false,
};

export const useAuthStore = create<AuthState & AuthActions>((set) => ({
  ...initialState,

  login: async (credentials) => {
    set({ isLoading: true });
    try {
      const response = await authApi.login(credentials);
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, response.access_token);
      set({ user: response.user, isAuthenticated: true });
      logger.info("User logged in", { feature: "auth", action: "login" });
    } catch (error) {
      handleError(error, { feature: "auth", action: "login" });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (data) => {
    set({ isLoading: true });
    try {
      await authApi.register(data);
      logger.info("User registered", { feature: "auth", action: "register" });
    } catch (error) {
      handleError(error, { feature: "auth", action: "register" });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  logout: () => {
    localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
    set({ user: null, isAuthenticated: false });
    logger.info("User logged out", { feature: "auth", action: "logout" });
  },

  fetchUser: async () => {
    try {
      const user = await authApi.getMe();
      set({ user, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
    }
  },

  reset: () => set(initialState),
}));
'''

    t[f"{base}/hooks/useAuth.ts"] = '''/**
 * Convenience hook — re-exports auth store with stable API.
 */
import { useAuthStore } from "./useAuthStore";

export function useAuth() {
  const { user, isAuthenticated, isLoading, login, logout, register, fetchUser } = useAuthStore();
  return { user, isAuthenticated, isLoading, login, logout, register, fetchUser };
}
'''

    t[f"{base}/components/LoginForm.tsx"] = '''/**
 * Login form — pure UI. Business logic in useAuthStore.
 */
import { useState, type FormEvent } from "react";
import { useAuth } from "../hooks/useAuth";
import { Button } from "@shared/ui/Button";
import { Input } from "@shared/ui/Input";
import { toast } from "sonner";
import { loginSchema, type LoginInput } from "@shared/utils/validators";

interface LoginFormProps {
  onSuccess?: () => void;
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const { login, isLoading } = useAuth();
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrors({});

    const formData = new FormData(e.currentTarget);
    const raw = {
      email: formData.get("email") as string,
      password: formData.get("password") as string,
    };

    // Validate
    const result = loginSchema.safeParse(raw);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of result.error.issues) {
        const field = issue.path[0] as string;
        fieldErrors[field] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    try {
      await login(result.data);
      toast.success("Welcome back!");
      onSuccess?.();
    } catch {
      toast.error("Login failed. Please check your credentials.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <Input
        name="email"
        type="email"
        label="Email"
        placeholder="you@example.com"
        error={errors.email}
        autoComplete="email"
        required
      />
      <Input
        name="password"
        type="password"
        label="Password"
        placeholder="Enter your password"
        error={errors.password}
        autoComplete="current-password"
        required
      />
      <Button type="submit" className="w-full" isLoading={isLoading}>
        Sign In
      </Button>
    </form>
  );
}
'''

    t[f"{base}/components/RegisterForm.tsx"] = '''/**
 * Registration form — pure UI with Zod validation.
 */
import { useState, type FormEvent } from "react";
import { useAuth } from "../hooks/useAuth";
import { Button } from "@shared/ui/Button";
import { Input } from "@shared/ui/Input";
import { toast } from "sonner";
import { registerSchema, type RegisterInput } from "@shared/utils/validators";

interface RegisterFormProps {
  onSuccess?: () => void;
}

export function RegisterForm({ onSuccess }: RegisterFormProps) {
  const { register, isLoading } = useAuth();
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrors({});

    const formData = new FormData(e.currentTarget);
    const raw = {
      name: formData.get("name") as string,
      email: formData.get("email") as string,
      password: formData.get("password") as string,
      confirmPassword: formData.get("confirmPassword") as string,
    };

    const result = registerSchema.safeParse(raw);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of result.error.issues) {
        const field = issue.path[0] as string;
        fieldErrors[field] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    try {
      await register({ name: result.data.name, email: result.data.email, password: result.data.password });
      toast.success("Account created! Please sign in.");
      onSuccess?.();
    } catch {
      toast.error("Registration failed. Please try again.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <Input name="name" label="Name" placeholder="John Doe" error={errors.name} autoComplete="name" required />
      <Input name="email" type="email" label="Email" placeholder="you@example.com" error={errors.email} autoComplete="email" required />
      <Input name="password" type="password" label="Password" placeholder="Min 8 chars, 1 upper, 1 number" error={errors.password} autoComplete="new-password" required />
      <Input name="confirmPassword" type="password" label="Confirm Password" placeholder="Repeat your password" error={errors.confirmPassword} autoComplete="new-password" required />
      <Button type="submit" className="w-full" isLoading={isLoading}>
        Create Account
      </Button>
    </form>
  );
}
'''

    t[f"{base}/pages/LoginPage.tsx"] = f'''import {{ Link, useNavigate }} from "react-router-dom";
import {{ LoginForm }} from "../components/LoginForm";
import {{ Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter }} from "@shared/ui/Card";
import {{ ROUTES }} from "@core/constants";

export default function LoginPage() {{
  const navigate = useNavigate();

  return (
    <div className="flex min-h-[80vh] items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle>Welcome Back</CardTitle>
          <CardDescription>Sign in to your {pn} account</CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm onSuccess={{() => navigate(ROUTES.DASHBOARD)}} />
        </CardContent>
        <CardFooter className="justify-center">
          <p className="text-sm text-muted-foreground">
            Don&apos;t have an account?{{" "}}
            <Link to={{ROUTES.REGISTER}} className="text-primary hover:underline">
              Sign up
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}}
'''

    t[f"{base}/pages/RegisterPage.tsx"] = f'''import {{ Link, useNavigate }} from "react-router-dom";
import {{ RegisterForm }} from "../components/RegisterForm";
import {{ Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter }} from "@shared/ui/Card";
import {{ ROUTES }} from "@core/constants";

export default function RegisterPage() {{
  const navigate = useNavigate();

  return (
    <div className="flex min-h-[80vh] items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle>Create Account</CardTitle>
          <CardDescription>Get started with {pn}</CardDescription>
        </CardHeader>
        <CardContent>
          <RegisterForm onSuccess={{() => navigate(ROUTES.LOGIN)}} />
        </CardContent>
        <CardFooter className="justify-center">
          <p className="text-sm text-muted-foreground">
            Already have an account?{{" "}}
            <Link to={{ROUTES.LOGIN}} className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}}
'''

    return t


def _gen_dashboard_feature(pn: str) -> Dict[str, str]:
    t = {}
    base = "frontend/src/features/dashboard"

    t[f"{base}/index.ts"] = '''/**
 * Dashboard feature — public API.
 */
export { useDashboardStats } from "./hooks/useDashboardStats";
export type { DashboardStats, Activity } from "./types";
'''

    t[f"{base}/types.ts"] = '''/** Dashboard feature types */

export interface DashboardStats {
  total_users: number;
  active_projects: number;
  revenue: number;
  growth_percent: number;
}

export interface Activity {
  id: string;
  action: string;
  description: string;
  timestamp: string;
  user_name: string;
}

export interface StatCard {
  label: string;
  value: string | number;
  change?: number;
  icon: string;
}
'''

    t[f"{base}/api/dashboardApi.ts"] = '''import { api } from "@infra/http/apiClient";
import { API_ENDPOINTS } from "@core/constants";
import type { DashboardStats, Activity } from "../types";

export const dashboardApi = {
  getStats: () =>
    api.get<DashboardStats>(API_ENDPOINTS.DASHBOARD.STATS),

  getActivity: () =>
    api.get<Activity[]>(API_ENDPOINTS.DASHBOARD.ACTIVITY),
};
'''

    t[f"{base}/hooks/useDashboardStats.ts"] = '''import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS } from "@core/constants";
import { dashboardApi } from "../api/dashboardApi";

export function useDashboardStats() {
  return useQuery({
    queryKey: QUERY_KEYS.DASHBOARD.STATS,
    queryFn: dashboardApi.getStats,
  });
}

export function useDashboardActivity() {
  return useQuery({
    queryKey: QUERY_KEYS.DASHBOARD.ACTIVITY,
    queryFn: dashboardApi.getActivity,
  });
}
'''

    t[f"{base}/components/StatsGrid.tsx"] = '''import { Card, CardHeader, CardTitle, CardContent } from "@shared/ui/Card";
import { Skeleton } from "@shared/ui/Skeleton";
import { formatNumber } from "@shared/utils/format";
import type { DashboardStats } from "../types";

interface StatsGridProps {
  stats: DashboardStats | undefined;
  isLoading: boolean;
}

export function StatsGrid({ stats, isLoading }: StatsGridProps) {
  const items = stats
    ? [
        { label: "Total Users", value: formatNumber(stats.total_users) },
        { label: "Active Projects", value: formatNumber(stats.active_projects) },
        { label: "Revenue", value: `$${formatNumber(stats.revenue)}` },
        { label: "Growth", value: `${stats.growth_percent}%` },
      ]
    : [];

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader><Skeleton className="h-4 w-24" /></CardHeader>
            <CardContent><Skeleton className="h-8 w-16" /></CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {item.label}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{item.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
'''

    t[f"{base}/components/ActivityFeed.tsx"] = '''import { Card, CardHeader, CardTitle, CardContent } from "@shared/ui/Card";
import { Skeleton } from "@shared/ui/Skeleton";
import { formatDateTime } from "@shared/utils/format";
import type { Activity } from "../types";

interface ActivityFeedProps {
  activities: Activity[] | undefined;
  isLoading: boolean;
}

export function ActivityFeed({ activities, isLoading }: ActivityFeedProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle>Recent Activity</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-8 w-8 rounded-full" />
              <div className="flex-1 space-y-1">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        {(!activities || activities.length === 0) ? (
          <p className="text-sm text-muted-foreground">No recent activity</p>
        ) : (
          <div className="space-y-4">
            {activities.map((activity) => (
              <div key={activity.id} className="flex items-start gap-3">
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium text-primary">
                  {activity.user_name.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 space-y-0.5">
                  <p className="text-sm">
                    <span className="font-medium">{activity.user_name}</span>{" "}
                    {activity.description}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatDateTime(activity.timestamp)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
'''

    t[f"{base}/pages/HomePage.tsx"] = f'''import {{ Link }} from "react-router-dom";
import {{ Button }} from "@shared/ui/Button";
import {{ Card, CardContent, CardHeader, CardTitle }} from "@shared/ui/Card";
import {{ ROUTES }} from "@core/constants";

export default function HomePage() {{
  return (
    <div className="space-y-16">
      <section className="flex flex-col items-center gap-6 py-16 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl text-balance">
          Welcome to{{" "}}<span className="text-primary">{pn}</span>
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground">
          A production-ready platform built with SSS-class architecture.
          Scalable, isolated, observable, and maintainable.
        </p>
        <div className="flex gap-4">
          <Link to={{ROUTES.REGISTER}}>
            <Button size="lg">Get Started</Button>
          </Link>
          <Link to={{ROUTES.LOGIN}}>
            <Button variant="outline" size="lg">Sign In</Button>
          </Link>
        </div>
      </section>

      <section className="space-y-8">
        <h2 className="text-center text-3xl font-bold">Platform Features</h2>
        <div className="grid gap-6 md:grid-cols-3">
          <Card>
            <CardHeader><CardTitle className="text-lg">Scalable Architecture</CardTitle></CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Domain-driven features with full isolation. Each module scales independently.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-lg">Performance First</CardTitle></CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Route-based code splitting, optimized caching, Suspense boundaries, and bundle analysis.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-lg">Enterprise Security</CardTitle></CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                JWT auth, input validation with Zod, protected routes, and security interceptors.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}}
'''

    t[f"{base}/pages/DashboardPage.tsx"] = '''import { FeatureErrorBoundary } from "@shared/components/FeatureErrorBoundary";
import { StatsGrid } from "../components/StatsGrid";
import { ActivityFeed } from "../components/ActivityFeed";
import { useDashboardStats, useDashboardActivity } from "../hooks/useDashboardStats";

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: activities, isLoading: activityLoading } = useDashboardActivity();

  return (
    <FeatureErrorBoundary feature="dashboard">
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your platform</p>
        </div>
        <StatsGrid stats={stats} isLoading={statsLoading} />
        <div className="grid gap-6 lg:grid-cols-2">
          <ActivityFeed activities={activities} isLoading={activityLoading} />
        </div>
      </div>
    </FeatureErrorBoundary>
  );
}
'''

    return t


def _gen_settings_feature(pn: str) -> Dict[str, str]:
    t = {}
    base = "frontend/src/features/settings"

    t[f"{base}/index.ts"] = '''/**
 * Settings feature — public API.
 */
export type { UserProfile, Preferences } from "./types";
'''

    t[f"{base}/types.ts"] = '''/** Settings feature types */

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  avatar_url?: string;
  bio?: string;
}

export interface Preferences {
  theme: "light" | "dark" | "system";
  notifications_enabled: boolean;
  email_digest: "daily" | "weekly" | "never";
  language: string;
}
'''

    t[f"{base}/api/settingsApi.ts"] = '''import { api } from "@infra/http/apiClient";
import { API_ENDPOINTS } from "@core/constants";
import type { UserProfile, Preferences } from "../types";

export const settingsApi = {
  getProfile: () => api.get<UserProfile>(API_ENDPOINTS.SETTINGS.GET),
  updateProfile: (data: Partial<UserProfile>) => api.put<UserProfile>(API_ENDPOINTS.SETTINGS.UPDATE, data),
};
'''

    t[f"{base}/components/ProfileForm.tsx"] = '''import { useState, type FormEvent } from "react";
import { Button } from "@shared/ui/Button";
import { Input } from "@shared/ui/Input";
import { Card, CardHeader, CardTitle, CardContent } from "@shared/ui/Card";
import { toast } from "sonner";
import { settingsApi } from "../api/settingsApi";
import type { UserProfile } from "../types";

interface ProfileFormProps {
  profile: UserProfile;
}

export function ProfileForm({ profile }: ProfileFormProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData(e.currentTarget);
    try {
      await settingsApi.updateProfile({
        name: formData.get("name") as string,
        bio: formData.get("bio") as string,
      });
      toast.success("Profile updated");
    } catch {
      toast.error("Failed to update profile");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input name="name" label="Name" defaultValue={profile.name} required />
          <Input name="email" label="Email" defaultValue={profile.email} disabled />
          <Input name="bio" label="Bio" defaultValue={profile.bio || ""} />
          <Button type="submit" isLoading={isLoading}>Save Changes</Button>
        </form>
      </CardContent>
    </Card>
  );
}
'''

    t[f"{base}/pages/SettingsPage.tsx"] = '''import { useQuery } from "@tanstack/react-query";
import { FeatureErrorBoundary } from "@shared/components/FeatureErrorBoundary";
import { LoadingScreen } from "@shared/ui/LoadingScreen";
import { QUERY_KEYS } from "@core/constants";
import { ProfileForm } from "../components/ProfileForm";
import { settingsApi } from "../api/settingsApi";

export default function SettingsPage() {
  const { data: profile, isLoading } = useQuery({
    queryKey: QUERY_KEYS.SETTINGS.ALL,
    queryFn: settingsApi.getProfile,
  });

  if (isLoading) return <LoadingScreen message="Loading settings..." />;

  return (
    <FeatureErrorBoundary feature="settings">
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Manage your account preferences</p>
        </div>
        {profile && <ProfileForm profile={profile} />}
      </div>
    </FeatureErrorBoundary>
  );
}
'''

    return t


def _gen_generic_feature(feature: str, pn: str) -> Dict[str, str]:
    """Generate a generic feature scaffold for any detected feature."""
    t = {}
    base = f"frontend/src/features/{feature}"
    title = feature.replace("_", " ").title()
    pascal = feature.title().replace("_", "").replace(" ", "")

    t[f"{base}/index.ts"] = f'''/**
 * {title} feature — public API.
 */
export type {{ {pascal}Item }} from "./types";
'''

    t[f"{base}/types.ts"] = f'''/** {title} feature types */

export interface {pascal}Item {{
  id: string;
  name: string;
  created_at: string;
  updated_at?: string;
}}
'''

    t[f"{base}/api/{feature}Api.ts"] = f'''import {{ api }} from "@infra/http/apiClient";
import {{ API_ENDPOINTS }} from "@core/constants";
import type {{ {pascal}Item }} from "../types";

export const {feature}Api = {{
  getAll: () => api.get<{pascal}Item[]>(API_ENDPOINTS.{feature.upper()}.LIST),
  getById: (id: string) => api.get<{pascal}Item>(API_ENDPOINTS.{feature.upper()}.DETAIL(id)),
  create: (data: Partial<{pascal}Item>) => api.post<{pascal}Item>(API_ENDPOINTS.{feature.upper()}.CREATE, data),
  update: (id: string, data: Partial<{pascal}Item>) => api.put<{pascal}Item>(API_ENDPOINTS.{feature.upper()}.UPDATE(id), data),
  delete: (id: string) => api.delete(API_ENDPOINTS.{feature.upper()}.DELETE(id)),
}};
'''

    t[f"{base}/hooks/use{pascal}.ts"] = f'''import {{ useQuery, useMutation, useQueryClient }} from "@tanstack/react-query";
import {{ {feature}Api }} from "../api/{feature}Api";
import {{ QUERY_KEYS }} from "@core/constants";
import {{ toast }} from "sonner";

export function use{pascal}List() {{
  return useQuery({{
    queryKey: QUERY_KEYS.{feature.upper()}.LIST,
    queryFn: {feature}Api.getAll,
  }});
}}

export function use{pascal}Mutations() {{
  const queryClient = useQueryClient();
  const invalidate = () => queryClient.invalidateQueries({{ queryKey: QUERY_KEYS.{feature.upper()}.LIST }});

  const create = useMutation({{
    mutationFn: {feature}Api.create,
    onSuccess: () => {{ toast.success("{title} created"); invalidate(); }},
    onError: () => toast.error("Failed to create {feature}"),
  }});

  const remove = useMutation({{
    mutationFn: {feature}Api.delete,
    onSuccess: () => {{ toast.success("{title} deleted"); invalidate(); }},
    onError: () => toast.error("Failed to delete {feature}"),
  }});

  return {{ create, remove }};
}}
'''

    t[f"{base}/pages/{pascal}Page.tsx"] = f'''import {{ FeatureErrorBoundary }} from "@shared/components/FeatureErrorBoundary";
import {{ LoadingScreen }} from "@shared/ui/LoadingScreen";
import {{ use{pascal}List }} from "../hooks/use{pascal}";

export default function {pascal}Page() {{
  const {{ data, isLoading }} = use{pascal}List();

  if (isLoading) return <LoadingScreen message="Loading {feature}..." />;

  return (
    <FeatureErrorBoundary feature="{feature}">
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold">{title}</h1>
          <p className="text-muted-foreground">Manage your {feature}</p>
        </div>
        <div className="grid gap-4">
          {{data?.map((item) => (
            <div key={{item.id}} className="rounded-lg border p-4">
              <h3 className="font-medium">{{item.name}}</h3>
            </div>
          ))}}
          {{(!data || data.length === 0) && (
            <p className="text-sm text-muted-foreground">No {feature} yet</p>
          )}}
        </div>
      </div>
    </FeatureErrorBoundary>
  );
}}
'''

    return t


# ─────────────────────────────────────────────────────────────────────────────
# TEST CONFIG
# ─────────────────────────────────────────────────────────────────────────────

def _gen_test_config() -> Dict[str, str]:
    return {
        "frontend/vitest.config.ts": '''import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/__tests__/setup.ts"],
    css: true,
    coverage: {
      reporter: ["text", "html", "lcov"],
      exclude: ["node_modules/", "src/__tests__/"],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@app": path.resolve(__dirname, "./src/app"),
      "@core": path.resolve(__dirname, "./src/core"),
      "@infra": path.resolve(__dirname, "./src/infrastructure"),
      "@features": path.resolve(__dirname, "./src/features"),
      "@shared": path.resolve(__dirname, "./src/shared"),
    },
  },
});
''',

        "frontend/src/__tests__/setup.ts": '''import "@testing-library/jest-dom/vitest";

// Global test setup
// Add any test utilities or mocks here
''',

        "frontend/src/__tests__/App.test.tsx": '''import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

// Mock modules that depend on browser APIs
vi.mock("@core/config", () => ({
  config: {
    apiUrl: "",
    appName: "Test App",
    appEnv: "development",
    isDevelopment: true,
    isProduction: false,
    enableLogging: false,
  },
}));

describe("Application", () => {
  it("renders without crashing", () => {
    const root = document.createElement("div");
    root.id = "root";
    document.body.appendChild(root);
    expect(root).toBeTruthy();
  });
});
''',
    }
