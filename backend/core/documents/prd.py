"""
Product Requirements Document (PRD) - MetaGPT-style
Created by ProductManager agent from user ideas
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from .base import Document, DocumentType


class UserStory(BaseModel):
    """A user story in the PRD"""
    id: str
    as_a: str  # "As a [user type]"
    i_want: str  # "I want [feature]"
    so_that: str  # "So that [benefit]"
    acceptance_criteria: List[str]
    priority: int = Field(ge=1, le=5, description="1=highest, 5=lowest")
    estimated_complexity: str = "medium"  # low, medium, high

    def to_markdown(self) -> str:
        """Convert user story to markdown"""
        md = f"### {self.id} (Priority: {self.priority}, Complexity: {self.estimated_complexity})\n\n"
        md += f"**As a** {self.as_a}\n\n"
        md += f"**I want** {self.i_want}\n\n"
        md += f"**So that** {self.so_that}\n\n"
        md += "**Acceptance Criteria:**\n"
        for criteria in self.acceptance_criteria:
            md += f"- {criteria}\n"
        md += "\n"
        return md


class TechConstraint(BaseModel):
    """Technical constraint or preference"""
    category: str  # "language", "framework", "deployment", "database", etc.
    constraint: str
    reason: str

    def to_markdown(self) -> str:
        return f"- **{self.category}**: {self.constraint}\n  - *Reason*: {self.reason}\n"


class SuccessMetric(BaseModel):
    """Measurable success metric"""
    metric: str
    target: str
    measurement_method: str

    def to_markdown(self) -> str:
        return f"- **{self.metric}**: {self.target}\n  - *Measurement*: {self.measurement_method}\n"


class PRDContent(BaseModel):
    """Content structure for PRD"""
    project_name: str
    project_description: str
    target_users: List[str]
    user_stories: List[UserStory] = Field(..., min_length=1)
    success_metrics: List[SuccessMetric]
    constraints: List[TechConstraint] = []
    out_of_scope: List[str] = []
    assumptions: List[str] = []
    timeline: Optional[str] = None
    budget: Optional[str] = None

    @field_validator('user_stories')
    @classmethod
    def validate_user_stories(cls, v: List[UserStory]) -> List[UserStory]:
        if len(v) == 0:
            raise ValueError("PRD must have at least one user story")
        return v

    @field_validator('project_name')
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Project name is required")
        return v.strip()


class PRDDocument(Document):
    """
    Product Requirements Document

    Created by ProductManager agent based on user idea.
    Serves as the foundation for all subsequent design and implementation.
    """
    doc_type: DocumentType = DocumentType.PRD
    content: PRDContent

    def to_markdown(self) -> str:
        """Convert PRD to markdown for agent consumption"""
        c = self.content

        md = f"# Product Requirements Document: {c.project_name}\n\n"
        md += f"**Document ID**: {self.doc_id}\n"
        md += f"**Created by**: {self.created_by}\n"
        md += f"**Version**: {self.version}\n"
        md += f"**Status**: {self.status}\n"
        if self.approved:
            md += f"**Approved by**: {self.approved_by}\n"
        md += "\n"

        md += "## Project Overview\n\n"
        md += f"{c.project_description}\n\n"

        if c.timeline:
            md += f"**Timeline**: {c.timeline}\n\n"
        if c.budget:
            md += f"**Budget**: {c.budget}\n\n"

        md += "## Target Users\n\n"
        for user in c.target_users:
            md += f"- {user}\n"
        md += "\n"

        md += "## User Stories\n\n"
        for story in c.user_stories:
            md += story.to_markdown()

        md += "## Success Metrics\n\n"
        for metric in c.success_metrics:
            md += metric.to_markdown()
        md += "\n"

        if c.constraints:
            md += "## Technical Constraints\n\n"
            for constraint in c.constraints:
                md += constraint.to_markdown()
            md += "\n"

        if c.out_of_scope:
            md += "## Out of Scope\n\n"
            for item in c.out_of_scope:
                md += f"- {item}\n"
            md += "\n"

        if c.assumptions:
            md += "## Assumptions\n\n"
            for assumption in c.assumptions:
                md += f"- {assumption}\n"
            md += "\n"

        if self.review_comments:
            md += "## Review Comments\n\n"
            for comment in self.review_comments:
                md += f"- {comment}\n"
            md += "\n"

        return md

    def validate_schema(self) -> bool:
        """Validate PRD structure"""
        try:
            # Check all required fields are present
            assert self.content.project_name
            assert self.content.project_description
            assert len(self.content.user_stories) > 0
            assert len(self.content.target_users) > 0

            # Validate user stories
            for story in self.content.user_stories:
                assert story.as_a
                assert story.i_want
                assert story.so_that
                assert len(story.acceptance_criteria) > 0
                assert 1 <= story.priority <= 5

            return True
        except (AssertionError, Exception):
            return False

    def get_high_priority_stories(self) -> List[UserStory]:
        """Get high priority user stories (priority 1-2)"""
        return [s for s in self.content.user_stories if s.priority <= 2]

    def get_feature_count(self) -> int:
        """Get total number of features (user stories)"""
        return len(self.content.user_stories)

    def estimate_complexity(self) -> str:
        """Estimate overall project complexity"""
        complexities = [s.estimated_complexity for s in self.content.user_stories]
        high_count = complexities.count("high")
        medium_count = complexities.count("medium")

        if high_count >= len(complexities) / 2:
            return "high"
        elif high_count > 0 or medium_count >= len(complexities) / 2:
            return "medium"
        else:
            return "low"
