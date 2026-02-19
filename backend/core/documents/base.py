"""
Document Base Classes - Foundation for document-driven development
Based on MetaGPT/Atmos document flow architecture
"""

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from uuid import uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentType(str, Enum):
    """All document types in the agent society"""
    PRD = "product_requirements"
    SYSTEM_DESIGN = "system_design"
    API_SPEC = "api_specification"
    TASKS = "task_breakdown"
    CODE = "code_implementation"
    TEST_PLAN = "test_plan"
    DEPLOYMENT = "deployment_guide"
    USER_DOCS = "user_documentation"


class DocumentVersion(BaseModel):
    """Version information for a document"""
    version_number: int
    created_at: datetime
    created_by: str
    changes_summary: str
    previous_version_id: Optional[str] = None


class Document(BaseModel):
    """
    Base document that flows through agent society.
    Every piece of information between agents is a formal document.
    """

    # Identity
    doc_id: str = Field(default_factory=lambda: f"doc_{uuid4().hex[:8]}")
    doc_type: DocumentType
    run_id: str  # Links to pipeline run

    # Versioning
    version: int = 1
    version_history: List[DocumentVersion] = []

    # Authorship
    created_by: str  # Agent name
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    # Content (override in subclasses)
    title: str
    content: Dict[str, Any]
    metadata: Dict[str, Any] = {}

    # Lineage tracking
    parent_doc_id: Optional[str] = None
    dependencies: List[str] = []  # doc_ids this depends on

    # Review & approval
    status: str = "draft"  # draft, review, approved, rejected
    approved: bool = False
    approved_by: Optional[str] = None
    review_comments: List[str] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_markdown(self) -> str:
        """Convert document to markdown for agent consumption"""
        md = f"# {self.title}\n\n"
        md += f"**Document ID**: {self.doc_id}\n"
        md += f"**Type**: {self.doc_type.value}\n"
        md += f"**Created by**: {self.created_by}\n"
        md += f"**Version**: {self.version}\n"
        md += f"**Status**: {self.status}\n\n"

        # Subclasses should override this to format their content
        md += "## Content\n\n"
        md += str(self.content)

        return md

    def create_new_version(self, changes: str, updated_by: str) -> Document:
        """Create a new version of this document"""
        new_version = self.model_copy(deep=True)
        new_version.version += 1
        new_version.version_history.append(
            DocumentVersion(
                version_number=self.version,
                created_at=self.created_at,
                created_by=self.created_by,
                changes_summary=changes,
                previous_version_id=self.doc_id
            )
        )
        new_version.doc_id = f"doc_{uuid4().hex[:8]}"
        new_version.created_by = updated_by
        new_version.updated_at = _utcnow()
        return new_version

    def validate_schema(self) -> bool:
        """Validate document structure - override in subclasses"""
        return True

    def approve(self, approved_by: str) -> None:
        """Approve this document"""
        self.approved = True
        self.approved_by = approved_by
        self.status = "approved"
        self.updated_at = _utcnow()

    def reject(self, rejected_by: str, reason: str) -> None:
        """Reject this document with feedback"""
        self.status = "rejected"
        self.review_comments.append(f"[{rejected_by}] {reason}")
        self.updated_at = _utcnow()


class DocumentStore:
    """
    Central storage for all documents.
    Provides versioning, indexing, and retrieval.
    """

    def __init__(self):
        self._documents: Dict[str, Document] = {}
        self._by_run: Dict[str, List[str]] = {}
        self._by_type: Dict[DocumentType, List[str]] = {}
        self._by_agent: Dict[str, List[str]] = {}

    def save(self, doc: Document) -> None:
        """Save a document"""
        self._documents[doc.doc_id] = doc

        # Index by run
        if doc.run_id not in self._by_run:
            self._by_run[doc.run_id] = []
        if doc.doc_id not in self._by_run[doc.run_id]:
            self._by_run[doc.run_id].append(doc.doc_id)

        # Index by type
        if doc.doc_type not in self._by_type:
            self._by_type[doc.doc_type] = []
        if doc.doc_id not in self._by_type[doc.doc_type]:
            self._by_type[doc.doc_type].append(doc.doc_id)

        # Index by agent
        if doc.created_by not in self._by_agent:
            self._by_agent[doc.created_by] = []
        if doc.doc_id not in self._by_agent[doc.created_by]:
            self._by_agent[doc.created_by].append(doc.doc_id)

    def get(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID"""
        return self._documents.get(doc_id)

    def get_by_run(self, run_id: str) -> List[Document]:
        """Get all documents for a run"""
        doc_ids = self._by_run.get(run_id, [])
        return [self._documents[did] for did in doc_ids if did in self._documents]

    def get_by_type(self, doc_type: DocumentType, run_id: Optional[str] = None) -> List[Document]:
        """Get documents by type, optionally filtered by run"""
        doc_ids = self._by_type.get(doc_type, [])
        docs = [self._documents[did] for did in doc_ids if did in self._documents]

        if run_id:
            docs = [d for d in docs if d.run_id == run_id]

        return docs

    def get_by_agent(self, agent_name: str, run_id: Optional[str] = None) -> List[Document]:
        """Get documents created by a specific agent"""
        doc_ids = self._by_agent.get(agent_name, [])
        docs = [self._documents[did] for did in doc_ids if did in self._documents]

        if run_id:
            docs = [d for d in docs if d.run_id == run_id]

        return docs

    def get_latest_version(self, doc_id: str) -> Optional[Document]:
        """Get the latest version of a document"""
        doc = self.get(doc_id)
        if not doc:
            return None

        # Follow the chain to find latest version
        all_versions = [doc]

        # Check all docs for this as parent
        for other_doc in self._documents.values():
            if other_doc.parent_doc_id == doc_id:
                all_versions.append(other_doc)

        return max(all_versions, key=lambda d: d.version)

    def get_approved_documents(self, run_id: str) -> List[Document]:
        """Get all approved documents for a run"""
        all_docs = self.get_by_run(run_id)
        return [d for d in all_docs if d.approved]

    def count_documents(self, run_id: Optional[str] = None, doc_type: Optional[DocumentType] = None) -> int:
        """Count documents with optional filters"""
        if run_id and doc_type:
            docs = self.get_by_type(doc_type, run_id)
        elif run_id:
            docs = self.get_by_run(run_id)
        elif doc_type:
            docs = self.get_by_type(doc_type)
        else:
            docs = list(self._documents.values())

        return len(docs)
