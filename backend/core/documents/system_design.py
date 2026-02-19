"""
System Design Document - MetaGPT-style
Created by Architect agent from PRD
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any
from .base import Document, DocumentType


class Component(BaseModel):
    """A system component"""
    name: str
    type: str  # "service", "database", "cache", "queue", "gateway", etc.
    description: str
    responsibilities: List[str]
    dependencies: List[str] = []
    tech_stack: Dict[str, str] = {}
    scalability_notes: Optional[str] = None

    def to_markdown(self) -> str:
        md = f"### {self.name} ({self.type})\n\n"
        md += f"{self.description}\n\n"
        md += "**Responsibilities:**\n"
        for resp in self.responsibilities:
            md += f"- {resp}\n"
        md += "\n"

        if self.dependencies:
            md += "**Dependencies:**\n"
            for dep in self.dependencies:
                md += f"- {dep}\n"
            md += "\n"

        if self.tech_stack:
            md += "**Tech Stack:**\n"
            for key, value in self.tech_stack.items():
                md += f"- {key}: {value}\n"
            md += "\n"

        if self.scalability_notes:
            md += f"**Scalability**: {self.scalability_notes}\n\n"

        return md


class DataModel(BaseModel):
    """A data model definition"""
    name: str
    description: str
    fields: Dict[str, str]  # field_name: type + description
    relationships: List[str] = []
    indexes: List[str] = []
    constraints: List[str] = []

    def to_markdown(self) -> str:
        md = f"### {self.name}\n\n"
        md += f"{self.description}\n\n"
        md += "**Fields:**\n"
        for field, desc in self.fields.items():
            md += f"- `{field}`: {desc}\n"
        md += "\n"

        if self.relationships:
            md += "**Relationships:**\n"
            for rel in self.relationships:
                md += f"- {rel}\n"
            md += "\n"

        if self.indexes:
            md += "**Indexes:**\n"
            for idx in self.indexes:
                md += f"- {idx}\n"
            md += "\n"

        if self.constraints:
            md += "**Constraints:**\n"
            for constraint in self.constraints:
                md += f"- {constraint}\n"
            md += "\n"

        return md


class APIEndpoint(BaseModel):
    """API endpoint definition"""
    path: str
    method: str  # GET, POST, PUT, DELETE, PATCH
    description: str
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    auth_required: bool = True
    rate_limit: Optional[str] = None

    def to_markdown(self) -> str:
        md = f"### {self.method} {self.path}\n\n"
        md += f"{self.description}\n\n"

        if self.auth_required:
            md += "*Requires authentication*\n\n"

        if self.rate_limit:
            md += f"*Rate limit: {self.rate_limit}*\n\n"

        if self.request_schema:
            md += "**Request:**\n```json\n"
            import json
            md += json.dumps(self.request_schema, indent=2)
            md += "\n```\n\n"

        if self.response_schema:
            md += "**Response:**\n```json\n"
            import json
            md += json.dumps(self.response_schema, indent=2)
            md += "\n```\n\n"

        return md


class SystemDesignContent(BaseModel):
    """Content for system design document"""
    architecture_pattern: str  # "monolith", "microservices", "serverless", "event-driven"
    architecture_diagram: str  # Mermaid diagram
    components: List[Component]
    data_models: List[DataModel]
    api_endpoints: List[APIEndpoint]
    deployment_model: str
    scaling_strategy: str
    security_considerations: List[str]
    performance_requirements: Dict[str, str]
    monitoring_strategy: Optional[str] = None
    disaster_recovery: Optional[str] = None

    @field_validator('architecture_pattern')
    @classmethod
    def validate_architecture_pattern(cls, v: str) -> str:
        valid_patterns = ["monolith", "microservices", "serverless", "event-driven", "layered"]
        if v not in valid_patterns:
            raise ValueError(f"Architecture pattern must be one of: {valid_patterns}")
        return v


class SystemDesignDocument(Document):
    """
    System Architecture Design Document

    Created by Architect agent based on PRD.
    Defines the technical architecture and system components.
    """
    doc_type: DocumentType = DocumentType.SYSTEM_DESIGN
    content: SystemDesignContent

    def to_markdown(self) -> str:
        """Convert system design to markdown"""
        c = self.content

        md = f"# System Design Document\n\n"
        md += f"**Document ID**: {self.doc_id}\n"
        md += f"**Created by**: {self.created_by}\n"
        md += f"**Version**: {self.version}\n"
        md += f"**Status**: {self.status}\n"
        md += f"**Architecture Pattern**: {c.architecture_pattern}\n\n"

        md += "## Architecture Overview\n\n"
        md += f"**Deployment Model**: {c.deployment_model}\n\n"
        md += f"**Scaling Strategy**: {c.scaling_strategy}\n\n"

        md += "## Architecture Diagram\n\n"
        md += "```mermaid\n"
        md += c.architecture_diagram
        md += "\n```\n\n"

        md += "## Components\n\n"
        for comp in c.components:
            md += comp.to_markdown()

        md += "## Data Models\n\n"
        for model in c.data_models:
            md += model.to_markdown()

        md += "## API Endpoints\n\n"
        for endpoint in c.api_endpoints:
            md += endpoint.to_markdown()

        md += "## Security Considerations\n\n"
        for security in c.security_considerations:
            md += f"- {security}\n"
        md += "\n"

        md += "## Performance Requirements\n\n"
        for key, value in c.performance_requirements.items():
            md += f"- **{key}**: {value}\n"
        md += "\n"

        if c.monitoring_strategy:
            md += "## Monitoring Strategy\n\n"
            md += f"{c.monitoring_strategy}\n\n"

        if c.disaster_recovery:
            md += "## Disaster Recovery\n\n"
            md += f"{c.disaster_recovery}\n\n"

        if self.review_comments:
            md += "## Review Comments\n\n"
            for comment in self.review_comments:
                md += f"- {comment}\n"
            md += "\n"

        return md

    def validate_schema(self) -> bool:
        """Validate system design structure"""
        try:
            assert self.content.architecture_pattern
            assert self.content.architecture_diagram
            assert len(self.content.components) > 0
            assert len(self.content.data_models) >= 0  # Can be empty for some apps
            assert self.content.deployment_model
            assert self.content.scaling_strategy
            return True
        except (AssertionError, Exception):
            return False

    def get_component_by_name(self, name: str) -> Optional[Component]:
        """Find a component by name"""
        for comp in self.content.components:
            if comp.name.lower() == name.lower():
                return comp
        return None

    def get_api_count(self) -> int:
        """Get total number of API endpoints"""
        return len(self.content.api_endpoints)

    def get_complexity_score(self) -> int:
        """Calculate complexity score based on components and APIs"""
        score = 0
        score += len(self.content.components) * 2
        score += len(self.content.data_models) * 1
        score += len(self.content.api_endpoints) * 1

        if self.content.architecture_pattern == "microservices":
            score += 10
        elif self.content.architecture_pattern == "serverless":
            score += 5

        return score
