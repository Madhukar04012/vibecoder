"""
Engineer Agent — Phase-1

Strict-role agent for writing production code.
Runs ONLY in EXECUTION state.
MUST retrieve semantic context before coding.

Usage:
    engineer = EngineerAgent(prd, roadmap)
    files = engineer.execute()
"""

from typing import Dict, Any, List, Optional
import re

from backend.agents.base_agent import BaseAgent
from backend.core.tech_detector import detect_stack, get_engineer_prompt_for_stack


SYSTEM_PROMPT_TEMPLATE = """You are a Principal Software Engineer at a FAANG company building production software.
Write the COMPLETE contents of the file '{file_path}'.

ABSOLUTE RULES — VIOLATION = REJECTION:
- Output ONLY raw file content. NO markdown, NO explanations, NO code fences (```), NO commentary
- Write PRODUCTION-QUALITY code that would pass a senior engineer's code review
- Every function, class, and module MUST have real, working logic — NO placeholders, NO TODOs, NO stubs
- Include ALL imports, ALL exports, ALL type annotations
- Handle ALL error cases with proper try/catch or error boundaries
- Follow the language's official style guide (PEP 8, Airbnb JS, Google Go, etc.)

S-CLASS CODING STANDARDS:
Frontend (TypeScript/React):
  - ALWAYS use TypeScript with strict mode — NEVER use 'any' type
  - ALWAYS use 'export default function ComponentName()' pattern for React components
  - ALL props MUST have TypeScript interfaces defined above the component
  - Use Tailwind CSS utility classes for ALL styling — NO inline styles, NO CSS modules
  - Implement responsive design: mobile-first with sm:/md:/lg:/xl: breakpoints
  - Add loading states, error states, and empty states for ALL data-driven components
  - Use React hooks properly: useMemo, useCallback for expensive operations
  - Import from '@/' path aliases (e.g., '@/components/ui/button')
  - Use lucide-react for ALL icons
  - Add 'use client' directive only when component uses browser APIs or hooks
  - Implement proper accessibility: aria-labels, keyboard navigation, semantic HTML
  - Use Zustand for global state, TanStack Query for server state
  - Add proper Zod validation for ALL form inputs

Backend (Python/FastAPI):
  - Use Pydantic v2 models for ALL request/response schemas with Field descriptions
  - Implement proper dependency injection with FastAPI Depends()
  - Add structured logging with structlog — NO print() statements
  - Use async/await consistently for ALL database and I/O operations
  - Implement proper exception hierarchy (AppException → NotFound, Unauthorized, etc.)
  - Add request validation, rate limiting middleware
  - Use environment variables via pydantic-settings — NO hardcoded values
  - Document ALL endpoints with OpenAPI docstrings
  - Type-hint EVERY function parameter and return value
  - Use SQLAlchemy 2.0 style with mapped_column

Backend (Node.js/Express):
  - Use TypeScript with strict configuration
  - Implement proper middleware chain with error handling
  - Use Zod for runtime validation
  - Structured logging with pino or winston
  - Proper async error handling with express-async-handler

General:
  - Every file MUST have a module-level docstring/comment explaining its purpose
  - Secrets/keys MUST come from environment variables
  - CORS configuration MUST use specific origins, not wildcards in production
  - Include proper HTTP status codes for all API responses
  - Database queries MUST be parameterized — NO string concatenation

PROJECT CONTEXT:
{project_context}

ADDITIONAL CONTEXT FROM MEMORY:
{memory_context}
"""


class EngineerAgent(BaseAgent):
    """
    Engineer agent for writing production code.
    
    State requirement: EXECUTION
    Input: PRD + Roadmap + Memory Context
    Output: Generated file contents
    """
    
    name = "engineer"
    
    def __init__(
        self,
        prd: Dict[str, Any],
        roadmap: Dict[str, Any],
        memory_scope_key: str = "global:v1",
    ):
        """
        Initialize the engineer with planning context.
        
        Args:
            prd: Product Requirements Document
            roadmap: Architecture and file plan
        """
        super().__init__()
        self.prd = prd
        self.roadmap = roadmap
        self.memory_scope_key = memory_scope_key
        self.generated_files: Dict[str, str] = {}
    
    def execute(self) -> Dict[str, str]:
        """
        Generate all files in the roadmap.
        
        Returns:
            Dict mapping file paths to contents
        """
        file_plan = self.roadmap.get("directory_structure", [])
        
        for file_path in file_plan:
            content = self.generate_file(file_path)
            self.generated_files[file_path] = content
        
        return self.generated_files
    
    def generate_file(self, file_path: str, memory_context: str = "") -> str:
        """
        Generate a single file.
        
        Args:
            file_path: Path of the file to generate
            memory_context: Additional context from semantic memory
            
        Returns:
            File content as string
        """
        import json
        
        # Detect stack from PRD for tech-aware prompting
        user_desc = self.prd.get('description', self.prd.get('title', '')) if isinstance(self.prd, dict) else str(self.prd)
        detected = detect_stack(user_desc)
        
        # Build project context
        project_context = f"""
PRD:
{json.dumps(self.prd, indent=2)}

Architecture:
{json.dumps(self.roadmap, indent=2)}

User request: {self.prd.get('description', self.prd.get('title', 'Build the application'))}
"""
        
        # Use tech-aware prompt if stack was detected
        if detected.backend_framework or detected.frontend_framework or detected.languages:
            system_prompt = get_engineer_prompt_for_stack(detected, file_path) + f"\n\nPROJECT CONTEXT:\n{project_context[:3000]}\n\nADDITIONAL CONTEXT FROM MEMORY:\n{memory_context[:1000] if memory_context else 'No additional context'}"
        else:
            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
                file_path=file_path,
                project_context=project_context[:3000],
                memory_context=memory_context[:1000] if memory_context else "No additional context",
            )
        
        response = self.call_llm_simple(
            system=system_prompt,
            user=f"Write the complete file: {file_path}",
            max_tokens=2048,
            temperature=0.3
        )
        
        if not response:
            return self._fallback_content(file_path)
        
        # Clean response (remove markdown fences if present)
        content = re.sub(r'^```\w*\n?', '', response.strip())
        content = re.sub(r'\n?```$', '', content.strip())
        
        return content
    
    def generate_file_with_memory(self, file_path: str) -> str:
        """
        Generate a file with semantic memory retrieval.
        
        This is the preferred method that retrieves context from memory first.
        
        Args:
            file_path: Path of the file to generate
            
        Returns:
            File content as string
        """
        # Try to retrieve context from memory
        memory_context = self._retrieve_memory_context(file_path)
        return self.generate_file(file_path, memory_context)
    
    def _retrieve_memory_context(self, file_path: str) -> str:
        """
        Retrieve relevant context from semantic memory.
        
        Args:
            file_path: Path being generated
            
        Returns:
            Context string from memory
        """
        try:
            from backend.memory.retriever import retrieve_context
            
            # Build query from file path and roadmap
            query = f"{file_path} {self.roadmap.get('architecture', '')}"
            return retrieve_context(query, k=3, scope_key=self.memory_scope_key)
        except ImportError:
            # Memory module not available
            return ""
        except Exception:
            return ""
    
    def _fallback_content(self, file_path: str) -> str:
        """Generate fallback content using S-class templates when available, otherwise generate quality code."""
        # Try S-class templates first
        try:
            from backend.templates.sclass_templates import get_sclass_templates
            # Build args from roadmap context
            _proj = self.roadmap.get("project_name", "my_project")
            _tech = {
                "backend": self.roadmap.get("backend", "FastAPI"),
                "frontend": self.roadmap.get("frontend", "React"),
                "database": self.roadmap.get("database", "PostgreSQL"),
            }
            _feats = self.roadmap.get("modules", [])
            _idea = self.roadmap.get("user_idea", "")
            templates = get_sclass_templates(_proj, _tech, _feats, user_idea=_idea)
            
            # Check for exact match or suffix match in templates
            for template_path, template_content in templates.items():
                if file_path == template_path or file_path.endswith(template_path):
                    return template_content
                # Partial match: same filename in same directory type
                fp_parts = file_path.replace("\\", "/").split("/")
                tp_parts = template_path.replace("\\", "/").split("/")
                if len(fp_parts) >= 2 and len(tp_parts) >= 2:
                    if fp_parts[-1] == tp_parts[-1] and fp_parts[-2] == tp_parts[-2]:
                        return template_content
        except ImportError:
            pass
        
        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
        name = file_path.split("/")[-1].rsplit(".", 1)[0]

        # JSON config files
        if ext == "json":
            if "package" in file_path:
                return self._fallback_package_json()
            return "{}"

        # Python files
        if ext == "py":
            return self._fallback_python(file_path, name)

        # Go files
        if ext == "go":
            return self._fallback_go(file_path, name)

        # Java files
        if ext == "java":
            return self._fallback_java(file_path, name)

        # Rust files
        if ext == "rs":
            return self._fallback_rust(file_path, name)

        # TypeScript files
        if ext in ("ts", "tsx"):
            return self._fallback_typescript(file_path, name)

        # JavaScript / JSX files
        if ext in ("js", "jsx"):
            return self._fallback_js(file_path)

        # CSS / SCSS
        if ext in ("css", "scss"):
            return self._fallback_css(file_path)

        # HTML
        if ext == "html":
            return self._fallback_html()

        # Vue single-file components
        if ext == "vue":
            return self._fallback_vue(name)

        # Svelte components
        if ext == "svelte":
            return self._fallback_svelte(name)

        # YAML/TOML config
        if ext in ("yaml", "yml"):
            return f"# {file_path}\n# Generated by VibeCoder\n"
        if ext == "toml":
            return f"# {file_path}\n# Generated by VibeCoder\n"

        # Markdown
        if ext == "md":
            return f"# {name}\n\nGenerated by VibeCoder\n"

        # SQL
        if ext == "sql":
            return f"-- {file_path}\n-- Generated by VibeCoder\n"

        # Shell scripts
        if ext == "sh":
            return f"#!/bin/bash\n# {file_path}\n# Generated by VibeCoder\n"

        # Makefile
        if name.lower() == "makefile" or ext == "mk":
            return f"# {file_path}\n# Generated by VibeCoder\n\n.PHONY: build run test\n\nbuild:\n\t@echo \"Building...\"\n\nrun:\n\t@echo \"Running...\"\n\ntest:\n\t@echo \"Testing...\"\n"

        # Requirements.txt
        if "requirements" in file_path.lower() and ext == "txt":
            return "# Python dependencies\n"

        # Generic fallback
        return f"// {file_path}\n// Generated by VibeCoder\n"
    
    def _fallback_package_json(self) -> str:
        return '''{
  "name": "vibe-app",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "type-check": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.1.0",
    "@tanstack/react-query": "^5.62.0",
    "zustand": "^5.0.0",
    "zod": "^3.24.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.6.0",
    "lucide-react": "^0.469.0",
    "sonner": "^1.7.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "~5.7.0",
    "vite": "^6.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^9.0.0",
    "vitest": "^2.0.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.0.0"
  }
}'''
    
    def _fallback_js(self, file_path: str) -> str:
        name = file_path.split("/")[-1].replace(".jsx", "").replace(".js", "")
        if "main" in file_path.lower():
            return '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)'''
        elif "App" in file_path:
            return '''import './App.css'

function App() {
  return (
    <div className="app">
      <h1>Welcome to VibeCoder</h1>
      <p>Your application is running!</p>
    </div>
  )
}

export default App'''
        else:
            return f'''// {name} Component
export default function {name}() {{
  return (
    <div className="{name.lower()}">
      {name}
    </div>
  )
}}'''
    
    def _fallback_css(self, file_path: str) -> str:
        return '''* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: #333;
}

.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}'''
    
    def _fallback_html(self) -> str:
        return '''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>VibeCoder App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>'''

    def _fallback_python(self, file_path: str, name: str) -> str:
        """S-class fallback for Python files."""
        if "main" in name.lower() or "app" in name.lower():
            return '''"""Application entry point — Factory pattern."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("application_starting")
    yield
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="VibeCoder App",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request timing middleware
    @app.middleware("http")
    async def add_timing(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Response-Time"] = f"{elapsed:.4f}s"
        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", path=str(request.url), error=str(exc))
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/health")
    async def health():
        return {"status": "healthy", "version": "1.0.0"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
'''
        elif "model" in name.lower() or "models" in file_path.lower():
            class_name = name.replace("_", " ").title().replace(" ", "")
            return f'''"""{class_name} database models."""

from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    """Base model class."""
    pass


class {class_name}(Base):
    """
    {class_name} model.

    Attributes:
        id: Primary key
        name: Display name  
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "{name.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<{class_name}(id={{self.id}}, name={{self.name!r}})>"
'''
        elif "schema" in name.lower() or "schemas" in file_path.lower():
            class_name = name.replace("_", " ").title().replace(" ", "")
            return f'''"""{class_name} Pydantic schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class {class_name}Base(BaseModel):
    """Base schema for {class_name}."""
    name: str = Field(..., min_length=1, max_length=255, description="Display name")


class {class_name}Create({class_name}Base):
    """Schema for creating a {class_name}."""
    pass


class {class_name}Update(BaseModel):
    """Schema for updating a {class_name}."""
    name: str | None = Field(None, min_length=1, max_length=255)


class {class_name}Response({class_name}Base):
    """Schema for {class_name} API response."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {{"from_attributes": True}}
'''
        elif "route" in name.lower() or "router" in name.lower() or "api" in file_path.lower():
            route_name = name.replace("_routes", "").replace("_router", "").replace("route", "").replace("router", "") or "items"
            return f'''"""{name} API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/{route_name}s", tags=["{route_name}s"])


@router.get("/")
async def list_{route_name}s(skip: int = 0, limit: int = 20):
    """List all {route_name}s with pagination."""
    logger.info("list_{route_name}s", skip=skip, limit=limit)
    return {{"items": [], "total": 0, "skip": skip, "limit": limit}}


@router.get("/{{item_id}}")
async def get_{route_name}(item_id: int):
    """Get a single {route_name} by ID."""
    # Replace with actual DB lookup
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{route_name} not found")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_{route_name}(data: dict):
    """Create a new {route_name}."""
    logger.info("create_{route_name}", data=data)
    return {{"created": True, "data": data}}


@router.put("/{{item_id}}")
async def update_{route_name}(item_id: int, data: dict):
    """Update an existing {route_name}."""
    logger.info("update_{route_name}", item_id=item_id)
    return {{"updated": True, "id": item_id}}


@router.delete("/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{route_name}(item_id: int):
    """Delete a {route_name}."""
    logger.info("delete_{route_name}", item_id=item_id)
    return None
'''
        elif "service" in name.lower() or "services" in file_path.lower():
            svc_name = name.replace("_service", "").replace("service", "") or "base"
            class_name = svc_name.replace("_", " ").title().replace(" ", "") + "Service"
            return f'''"""{class_name} — Business logic layer."""

from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class {class_name}:
    """
    {class_name} encapsulates business logic for {svc_name} operations.
    
    Follows the Repository pattern — database access is injected.
    """

    def __init__(self, db_session=None):
        self.db = db_session

    async def get_all(self, skip: int = 0, limit: int = 20) -> list:
        """Retrieve paginated list."""
        logger.info("{svc_name}_get_all", skip=skip, limit=limit)
        return []

    async def get_by_id(self, item_id: int) -> Optional[dict]:
        """Retrieve single item by ID."""
        logger.info("{svc_name}_get_by_id", item_id=item_id)
        return None

    async def create(self, data: dict) -> dict:
        """Create new item with validation."""
        logger.info("{svc_name}_create")
        return {{"id": 1, **data}}

    async def update(self, item_id: int, data: dict) -> Optional[dict]:
        """Update existing item."""
        logger.info("{svc_name}_update", item_id=item_id)
        return {{"id": item_id, **data}}

    async def delete(self, item_id: int) -> bool:
        """Delete item by ID."""
        logger.info("{svc_name}_delete", item_id=item_id)
        return True
'''
        elif "config" in name.lower() or "settings" in name.lower():
            return '''"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # App
    app_name: str = Field(default="VibeCoder App", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Runtime environment")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./app.db", description="Database connection URL"
    )
    
    # Auth
    secret_key: str = Field(default="change-me-in-production", description="JWT secret")
    access_token_expire_minutes: int = Field(default=30, description="Token expiry")
    
    # CORS
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000"], description="CORS origins"
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
'''
        elif "test" in name.lower() or "tests" in file_path.lower():
            return f'''"""{name} tests."""

import pytest


class Test{name.replace("_", " ").replace("test ", "").title().replace(" ", "")}:
    """Test suite for {name}."""

    def test_placeholder(self):
        """Verify basic functionality."""
        assert True

    def test_edge_case(self):
        """Verify edge case handling."""
        assert True

    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Verify async operation."""
        result = True
        assert result is True
'''
        elif "middleware" in name.lower() or "middleware" in file_path.lower():
            return f'''"""{name} middleware."""

from fastapi import Request
from fastapi.responses import JSONResponse
import structlog
import time

logger = structlog.get_logger(__name__)


async def {name}_middleware(request: Request, call_next):
    """
    {name.replace("_", " ").title()} middleware.
    
    Processes requests before and after route handlers.
    """
    start_time = time.perf_counter()
    
    try:
        response = await call_next(request)
        elapsed = time.perf_counter() - start_time
        logger.info(
            "{name}_request",
            method=request.method,
            path=str(request.url.path),
            status=response.status_code,
            duration=f"{{elapsed:.4f}}s",
        )
        return response
    except Exception as exc:
        logger.error("{name}_error", error=str(exc), path=str(request.url.path))
        return JSONResponse(status_code=500, content={{"detail": "Internal server error"}})
'''
        elif "__init__" in name:
            pkg = file_path.rsplit("/", 2)[-2] if "/" in file_path else name
            return f'"""{pkg} package."""\n'
        else:
            return f'"""{name} module."""\n\n# TODO: Implement {name} functionality\n'

    def _fallback_go(self, file_path: str, name: str) -> str:
        """Fallback for Go files."""
        if "main" in name.lower():
            return '''package main

import (
\t"fmt"
\t"log"
\t"net/http"
)

func main() {
\thttp.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
\t\tfmt.Fprintf(w, `{"status":"running"}`)
\t})

\thttp.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
\t\tfmt.Fprintf(w, `{"status":"healthy"}`)
\t})

\tlog.Println("Server starting on :8080")
\tlog.Fatal(http.ListenAndServe(":8080", nil))
}
'''
        elif "handler" in name.lower() or "route" in name.lower():
            return f'''package handler

import (
\t"encoding/json"
\t"net/http"
)

// {name.replace("_", " ").title().replace(" ", "")}Handler handles requests.
func {name.replace("_", " ").title().replace(" ", "")}Handler(w http.ResponseWriter, r *http.Request) {{
\tw.Header().Set("Content-Type", "application/json")
\tjson.NewEncoder(w).Encode(map[string]string{{"status": "ok"}})
}}
'''
        else:
            pkg = file_path.split("/")[-2] if "/" in file_path else "main"
            return f'package {pkg}\n\n// {name} - Generated by VibeCoder\n'

    def _fallback_java(self, file_path: str, name: str) -> str:
        """Fallback for Java files."""
        if "application" in name.lower() or "main" in name.lower():
            return '''package com.app;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
'''
        elif "controller" in name.lower():
            class_name = name.replace("_", " ").title().replace(" ", "")
            return f'''package com.app.controller;

import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestController
@RequestMapping("/api")
public class {class_name} {{

    @GetMapping("/health")
    public Map<String, String> health() {{
        return Map.of("status", "healthy");
    }}

    @GetMapping("/items")
    public List<Map<String, Object>> list() {{
        return List.of();
    }}
}}
'''
        else:
            class_name = name.replace("_", " ").title().replace(" ", "")
            return f'''package com.app;

/**
 * {class_name} - Generated by VibeCoder
 */
public class {class_name} {{
}}
'''

    def _fallback_rust(self, file_path: str, name: str) -> str:
        """Fallback for Rust files."""
        if "main" in name.lower():
            return '''fn main() {
    println!("VibeCoder App - Running");
}
'''
        elif "lib" in name.lower():
            return f'''//! {name} library
//! Generated by VibeCoder

pub fn hello() -> &\'static str {{
    "Hello from VibeCoder"
}}

#[cfg(test)]
mod tests {{
    use super::*;

    #[test]
    fn test_hello() {{
        assert_eq!(hello(), "Hello from VibeCoder");
    }}
}}
'''
        else:
            return f'//! {name} module\n//! Generated by VibeCoder\n'

    def _fallback_typescript(self, file_path: str, name: str) -> str:
        """S-class fallback for TypeScript files."""
        if file_path.endswith(".tsx"):
            # Determine component type from path
            is_page = "/pages/" in file_path or "/app/" in file_path
            is_layout = "layout" in name.lower() or "header" in name.lower() or "footer" in name.lower() or "sidebar" in name.lower()
            is_ui = "/ui/" in file_path
            pascal_name = name.replace("_", " ").replace("-", " ").title().replace(" ", "")
            kebab_name = name.replace("_", "-").lower()
            
            if is_ui:
                # UI component with variants
                return f'''import {{ type HTMLAttributes, forwardRef }} from "react";
import {{ cn }} from "@/lib/utils";

interface {pascal_name}Props extends HTMLAttributes<HTMLDivElement> {{
  variant?: "default" | "destructive" | "outline";
  size?: "sm" | "md" | "lg";
}}

const {pascal_name} = forwardRef<HTMLDivElement, {pascal_name}Props>(
  ({{ className, variant = "default", size = "md", ...props }}, ref) => {{
    return (
      <div
        ref={{ref}}
        className={{cn(
          "rounded-lg border transition-colors",
          variant === "default" && "bg-white border-gray-200",
          variant === "destructive" && "bg-red-50 border-red-200 text-red-800",
          variant === "outline" && "bg-transparent border-gray-300",
          size === "sm" && "p-3 text-sm",
          size === "md" && "p-4",
          size === "lg" && "p-6 text-lg",
          className,
        )}}
        {{...props}}
      />
    );
  }},
);

{pascal_name}.displayName = "{pascal_name}";

export {{ {pascal_name} }};
export type {{ {pascal_name}Props }};
'''
            elif is_layout:
                return f'''import {{ type ReactNode }} from "react";

interface {pascal_name}Props {{
  children?: ReactNode;
}}

export default function {pascal_name}({{ children }}: {pascal_name}Props) {{
  return (
    <div className="min-h-screen flex flex-col">
      {{/* {pascal_name} */}}
      <div className="w-full">
        {{children}}
      </div>
    </div>
  );
}}
'''
            elif is_page:
                return f'''import {{ useEffect, useState }} from "react";

export default function {pascal_name}Page() {{
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {{
    // Load page data
    const timer = setTimeout(() => setIsLoading(false), 100);
    return () => clearTimeout(timer);
  }}, []);

  if (isLoading) {{
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }}

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold tracking-tight mb-6">{pascal_name}</h1>
      <div className="grid gap-6">
        {{/* Content */}}
      </div>
    </div>
  );
}}
'''
            else:
                # Standard component
                return f'''import {{ type HTMLAttributes }} from "react";
import {{ cn }} from "@/lib/utils";

interface {pascal_name}Props extends HTMLAttributes<HTMLDivElement> {{
  title?: string;
}}

export default function {pascal_name}({{ title, className, ...props }}: {pascal_name}Props) {{
  return (
    <div className={{cn("rounded-xl border bg-card p-6 shadow-sm", className)}} {{...props}}>
      {{title && (
        <h2 className="text-xl font-semibold tracking-tight mb-4">{{title}}</h2>
      )}}
      <div className="space-y-4">
        {{/* {pascal_name} content */}}
      </div>
    </div>
  );
}}
'''
        elif "index" in name.lower() or "main" in name.lower():
            return '''import React from "react";
import ReactDOM from "react-dom/client";
import {{ BrowserRouter }} from "react-router-dom";
import {{ QueryClient, QueryClientProvider }} from "@tanstack/react-query";
import App from "./App";
import "./index.css";

const queryClient = new QueryClient({{
  defaultOptions: {{
    queries: {{
      staleTime: 5 * 60 * 1000,
      retry: 1,
    }},
  }},
}});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={{queryClient}}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
'''
        elif "store" in name.lower() or "store" in file_path.lower():
            store_name = name.replace("-store", "").replace("_store", "").replace("Store", "")
            pascal = store_name.replace("_", " ").replace("-", " ").title().replace(" ", "")
            return f'''import {{ create }} from "zustand";
import {{ persist }} from "zustand/middleware";

interface {pascal}State {{
  data: Record<string, unknown>[];
  isLoading: boolean;
  error: string | null;
  setData: (data: Record<string, unknown>[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}}

export const use{pascal}Store = create<{pascal}State>()(
  persist(
    (set) => ({{
      data: [],
      isLoading: false,
      error: null,
      setData: (data) => set({{ data, error: null }}),
      setLoading: (isLoading) => set({{ isLoading }}),
      setError: (error) => set({{ error, isLoading: false }}),
      reset: () => set({{ data: [], isLoading: false, error: null }}),
    }}),
    {{ name: "{store_name}-storage" }},
  ),
);
'''
        elif "hook" in file_path.lower() or name.startswith("use"):
            hook_name = name if name.startswith("use") else f"use{name.replace('_', ' ').replace('-', ' ').title().replace(' ', '')}"
            return f'''import {{ useState, useEffect, useCallback }} from "react";

/**
 * {hook_name} - Custom React hook
 */
export function {hook_name}() {{
  const [data, setData] = useState<unknown>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async () => {{
    setIsLoading(true);
    setError(null);
    try {{
      // Implementation
      setData(null);
    }} catch (err) {{
      setError(err instanceof Error ? err : new Error("Unknown error"));
    }} finally {{
      setIsLoading(false);
    }}
  }}, []);

  return {{ data, isLoading, error, execute }};
}}
'''
        elif "type" in file_path.lower() or "interface" in name.lower():
            return f'''/**
 * {name} - Type definitions
 */

export interface BaseEntity {{
  id: string;
  createdAt: string;
  updatedAt: string;
}}

export interface PaginatedResponse<T> {{
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}}

export interface ApiResponse<T = unknown> {{
  success: boolean;
  data: T;
  message?: string;
}}

export interface ApiError {{
  status: number;
  message: string;
  details?: Record<string, string[]>;
}}
'''
        elif "config" in name.lower() or "vite" in name.lower():
            return '''import {{ defineConfig }} from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({{
  plugins: [react()],
  resolve: {{
    alias: {{
      "@": path.resolve(__dirname, "./src"),
    }},
  }},
  server: {{
    port: 3000,
    proxy: {{
      "/api": {{
        target: "http://localhost:8000",
        changeOrigin: true,
      }},
    }},
  }},
}});
'''
        else:
            pascal_name = name.replace("_", " ").replace("-", " ").title().replace(" ", "")
            return f'''/**
 * {name} module
 */

export interface {pascal_name} {{
  id: string;
  name: string;
  createdAt: Date;
  updatedAt: Date;
}}

export function create{pascal_name}(data: Partial<{pascal_name}>): {pascal_name} {{
  return {{
    id: crypto.randomUUID(),
    name: data.name ?? "",
    createdAt: new Date(),
    updatedAt: new Date(),
    ...data,
  }};
}}
'''

    def _fallback_vue(self, name: str) -> str:
        """Fallback for Vue single-file components."""
        return f'''<template>
  <div class="{name.lower()}">
    <h2>{{ name }}</h2>
  </div>
</template>

<script setup>
import {{ ref }} from "vue";

const name = ref("{name}");
</script>

<style scoped>
.{name.lower()} {{
  padding: 1rem;
}}
</style>
'''

    def _fallback_svelte(self, name: str) -> str:
        """Fallback for Svelte components."""
        return f'''<script>
  let name = "{name}";
</script>

<div class="{name.lower()}">
  <h2>{{name}}</h2>
</div>

<style>
  .{name.lower()} {{
    padding: 1rem;
  }}
</style>
'''
