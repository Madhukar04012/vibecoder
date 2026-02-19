"""
Code Agent - Generates SSS-class project structure

Uses SSS-class platform architecture templates as the foundation for
React frontends, with S-class backend templates and legacy fallback
for non-standard stacks.

Architecture levels:
  SSS-class: Platform-grade (app/core/infrastructure/features/shared layers)
  S-class:   Production-grade (existing flat templates)
  Legacy:    Basic templates for non-React/non-Python stacks
"""

from backend.core.tech_detector import detect_stack


def code_agent(architecture: dict, user_idea: str = ""):
    """
    Takes architecture from planner and returns full project structure
    with production-quality SSS-class platform architecture.
    
    Strategy:
    1. Try SSS-class frontend + S-class backend for React+Python stacks
    2. Fall back to S-class templates if SSS-class import fails
    3. Fall back to legacy tech-aware templates for non-standard stacks
    
    The SSS-class frontend produces 80+ files organized into:
      - app/          → Composition layer (providers, routes, layouts)
      - core/         → Infrastructure (config, logger, errors, performance)
      - infrastructure/ → External systems (HTTP client, interceptors, WS)
      - features/     → Domain-driven isolated features
      - shared/       → Shared UI, hooks, utils, types
    """
    project_name = "my_project"
    
    backend_fw = architecture.get('backend', '')
    frontend_fw = architecture.get('frontend', '')
    stack_hint = f"{backend_fw} {frontend_fw} {architecture.get('database', '')}"
    detected = detect_stack(stack_hint)
    
    is_sclass_frontend = (
        not frontend_fw or
        frontend_fw.lower() in ("react", "react.js", "")  or
        "react" in stack_hint.lower()
    )
    is_sclass_backend = (
        not backend_fw or
        backend_fw.lower() in ("fastapi", "flask", "django", "") or
        detected.backend_language in ("python", None)
    )
    
    if is_sclass_frontend or is_sclass_backend:
        try:
            tech_stack = {
                "backend": architecture.get('backend', 'FastAPI'),
                "frontend": architecture.get('frontend', 'React'),
                "database": architecture.get('database', 'PostgreSQL')
            }
            features = architecture.get('modules', [])
            
            all_templates = {}
            
            # ── SSS-class frontend (platform architecture) ──
            if is_sclass_frontend and tech_stack.get("frontend", "").lower() != "none":
                try:
                    from backend.templates.sss_class_frontend import (
                        get_sss_class_frontend_templates,
                        plan_frontend_architecture,
                    )
                    # CTO-level planning happens inside get_sss_class_frontend_templates
                    sss_frontend = get_sss_class_frontend_templates(
                        project_name, features, user_idea
                    )
                    all_templates.update(sss_frontend)
                    print(f"[CODER] SSS-class frontend: {len(sss_frontend)} files generated")
                except ImportError:
                    # Fall back to S-class if SSS-class not available
                    from backend.templates.sclass_templates import get_sclass_frontend_templates
                    all_templates.update(get_sclass_frontend_templates(project_name, features))
                    print("[CODER] Fell back to S-class frontend templates")
            
            # ── S-class backend ──
            if is_sclass_backend and tech_stack.get("backend", "").lower() != "none":
                from backend.templates.sclass_templates import get_sclass_backend_templates
                all_templates.update(get_sclass_backend_templates(project_name, features))
            
            # ── Root / DevOps ──
            from backend.templates.sclass_templates import get_sclass_root_templates
            all_templates.update(get_sclass_root_templates(project_name, tech_stack))
            
            # Organize into nested project structure
            project = {}
            for path, content in all_templates.items():
                parts = path.replace("\\", "/").split("/")
                current = project
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = content
            
            print(f"[CODER] Total project files: {len(all_templates)}")
            return {project_name: project}
        except ImportError:
            pass
    
    # Fall back to legacy templates for non-standard stacks
    from backend.templates.code_templates import get_templates
    structure = get_templates(project_name, architecture)
    
    return structure
