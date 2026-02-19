"""Template Manager - reusable project templates (plan Phase 3.1)."""
from __future__ import annotations
from typing import Dict, Any, Optional, List

TEMPLATES: Dict[str, Dict[str, Any]] = {
    "saas_app": {
        "stack": {"frontend": "react", "backend": "fastapi", "db": "postgres"},
        "features": ["auth", "billing", "admin_panel", "api"],
        "architecture": "monolith",
        "deployment": "docker",
    },
    "ml_pipeline": {
        "stack": {"framework": "pytorch", "serving": "fastapi", "db": "mongodb"},
        "features": ["data_ingestion", "training", "inference", "monitoring"],
        "architecture": "event_driven",
    },
    "mobile_app": {
        "stack": {"mobile": "react_native", "backend": "firebase"},
        "features": ["auth", "push_notifications", "offline_mode"],
        "architecture": "serverless",
    },
    "web_app": {
        "stack": {"frontend": "react", "backend": "fastapi", "database": "postgres"},
        "features": ["auth", "crud", "api"],
        "architecture": "monolith",
        "deployment": "docker",
    },
}

class TemplateManager:
    def __init__(self) -> None:
        self.templates = dict(TEMPLATES)

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        return self.templates.get(name)

    def list_names(self) -> List[str]:
        return list(self.templates.keys())

    def create_spec(self, template_name: str, customizations: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        base = self.templates.get(template_name, {})
        spec = {**base}
        if customizations:
            for k, v in customizations.items():
                if isinstance(spec.get(k), dict) and isinstance(v, dict):
                    spec[k] = {**spec[k], **v}
                else:
                    spec[k] = v
        return spec
