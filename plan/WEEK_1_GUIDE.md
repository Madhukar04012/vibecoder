# Week 1 Implementation Guide
## Getting Started: Document-Driven Architecture

This guide provides concrete code to implement in Week 1-2 of the transformation plan.

---

## Day 1-2: Document Schema Foundation

### 1. Create Document Base Classes

**File: `backend/core/documents/base.py`**
```python
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

class DocumentType(str, Enum):
    """All document types in the system"""
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
    """Base document that flows through agent society"""
    
    # Identity
    doc_id: str = Field(default_factory=lambda: f"doc_{uuid4().hex[:8]}")
    doc_type: DocumentType
    run_id: str  # Links to pipeline run
    
    # Versioning
    version: int = 1
    version_history: List[DocumentVersion] = []
    
    # Authorship
    created_by: str  # Agent name
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
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
    
    def to_markdown(self) -> str:
        """Convert document to markdown for agent consumption"""
        md = f"# {self.title}\n\n"
        md += f"**Document ID**: {self.doc_id}\n"
        md += f"**Type**: {self.doc_type.value}\n"
        md += f"**Created by**: {self.created_by}\n"
        md += f"**Version**: {self.version}\n\n"
        
        # Subclasses should override this to format their content
        md += "## Content\n\n"
        md += str(self.content)
        
        return md
    
    def create_new_version(self, changes: str, updated_by: str) -> Document:
        """Create a new version of this document"""
        new_version = self.copy(deep=True)
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
        new_version.updated_at = datetime.utcnow()
        return new_version
    
    def validate_schema(self) -> bool:
        """Validate document structure - override in subclasses"""
        return True

class DocumentStore:
    """Central storage for all documents"""
    
    def __init__(self):
        self._documents: Dict[str, Document] = {}
        self._by_run: Dict[str, List[str]] = {}
        self._by_type: Dict[DocumentType, List[str]] = {}
    
    def save(self, doc: Document) -> None:
        """Save a document"""
        self._documents[doc.doc_id] = doc
        
        # Index by run
        if doc.run_id not in self._by_run:
            self._by_run[doc.run_id] = []
        self._by_run[doc.run_id].append(doc.doc_id)
        
        # Index by type
        if doc.doc_type not in self._by_type:
            self._by_type[doc.doc_type] = []
        self._by_type[doc.doc_type].append(doc.doc_id)
    
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
    
    def get_latest_version(self, doc_id: str) -> Optional[Document]:
        """Get the latest version of a document"""
        doc = self.get(doc_id)
        if not doc:
            return None
        
        # Follow the chain to find latest version
        # (In production, you'd want a better index for this)
        all_versions = [doc]
        
        # Simple approach: check all docs for this as parent
        for other_doc in self._documents.values():
            if other_doc.parent_doc_id == doc_id:
                all_versions.append(other_doc)
        
        return max(all_versions, key=lambda d: d.version)
```

### 2. Create Specific Document Types

**File: `backend/core/documents/prd.py`**
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from .base import Document, DocumentType

class UserStory(BaseModel):
    """A user story in the PRD"""
    id: str
    as_a: str  # "As a [user type]"
    i_want: str  # "I want [feature]"
    so_that: str  # "So that [benefit]"
    acceptance_criteria: List[str]
    priority: int = Field(ge=1, le=5)
    estimated_complexity: str = "medium"  # low, medium, high

class TechConstraint(BaseModel):
    """Technical constraint or preference"""
    category: str  # "language", "framework", "deployment", etc.
    constraint: str
    reason: str

class SuccessMetric(BaseModel):
    """Measurable success metric"""
    metric: str
    target: str
    measurement_method: str

class PRDContent(BaseModel):
    """Content structure for PRD"""
    project_name: str
    project_description: str
    target_users: List[str]
    user_stories: List[UserStory] = Field(min_items=1)
    success_metrics: List[SuccessMetric]
    constraints: List[TechConstraint] = []
    out_of_scope: List[str] = []
    assumptions: List[str] = []
    
    @validator('user_stories')
    def validate_user_stories(cls, v):
        if len(v) == 0:
            raise ValueError("PRD must have at least one user story")
        return v

class PRDDocument(Document):
    """Product Requirements Document"""
    doc_type: DocumentType = DocumentType.PRD
    content: PRDContent
    
    def to_markdown(self) -> str:
        """Convert PRD to markdown"""
        md = f"# Product Requirements Document: {self.content.project_name}\n\n"
        
        md += f"**Document ID**: {self.doc_id}\n"
        md += f"**Created by**: {self.created_by}\n"
        md += f"**Version**: {self.version}\n\n"
        
        md += "## Project Overview\n\n"
        md += f"{self.content.project_description}\n\n"
        
        md += "## Target Users\n\n"
        for user in self.content.target_users:
            md += f"- {user}\n"
        md += "\n"
        
        md += "## User Stories\n\n"
        for story in self.content.user_stories:
            md += f"### {story.id} (Priority: {story.priority})\n\n"
            md += f"**As a** {story.as_a}\n\n"
            md += f"**I want** {story.i_want}\n\n"
            md += f"**So that** {story.so_that}\n\n"
            md += "**Acceptance Criteria:**\n"
            for criteria in story.acceptance_criteria:
                md += f"- {criteria}\n"
            md += "\n"
        
        md += "## Success Metrics\n\n"
        for metric in self.content.success_metrics:
            md += f"- **{metric.metric}**: {metric.target}\n"
            md += f"  - *Measurement*: {metric.measurement_method}\n"
        md += "\n"
        
        if self.content.constraints:
            md += "## Technical Constraints\n\n"
            for constraint in self.content.constraints:
                md += f"- **{constraint.category}**: {constraint.constraint}\n"
                md += f"  - *Reason*: {constraint.reason}\n"
            md += "\n"
        
        if self.content.out_of_scope:
            md += "## Out of Scope\n\n"
            for item in self.content.out_of_scope:
                md += f"- {item}\n"
            md += "\n"
        
        return md
```

**File: `backend/core/documents/system_design.py`**
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from .base import Document, DocumentType

class Component(BaseModel):
    """A system component"""
    name: str
    type: str  # "service", "database", "cache", "queue", etc.
    description: str
    responsibilities: List[str]
    dependencies: List[str] = []
    tech_stack: Dict[str, str] = {}

class DataModel(BaseModel):
    """A data model definition"""
    name: str
    description: str
    fields: Dict[str, str]  # field_name: type
    relationships: List[str] = []
    indexes: List[str] = []

class APIEndpoint(BaseModel):
    """API endpoint definition"""
    path: str
    method: str  # GET, POST, PUT, DELETE
    description: str
    request_schema: Optional[Dict] = None
    response_schema: Optional[Dict] = None
    auth_required: bool = True

class SystemDesignContent(BaseModel):
    """Content for system design document"""
    architecture_pattern: str  # "monolith", "microservices", "serverless"
    architecture_diagram: str  # Mermaid diagram
    components: List[Component]
    data_models: List[DataModel]
    api_endpoints: List[APIEndpoint]
    deployment_model: str
    scaling_strategy: str
    security_considerations: List[str]
    performance_requirements: Dict[str, str]

class SystemDesignDocument(Document):
    """System Architecture Design"""
    doc_type: DocumentType = DocumentType.SYSTEM_DESIGN
    content: SystemDesignContent
    
    def to_markdown(self) -> str:
        """Convert system design to markdown"""
        md = f"# System Design Document\n\n"
        md += f"**Architecture Pattern**: {self.content.architecture_pattern}\n\n"
        
        md += "## Architecture Diagram\n\n"
        md += "```mermaid\n"
        md += self.content.architecture_diagram
        md += "\n```\n\n"
        
        md += "## Components\n\n"
        for comp in self.content.components:
            md += f"### {comp.name} ({comp.type})\n\n"
            md += f"{comp.description}\n\n"
            md += "**Responsibilities:**\n"
            for resp in comp.responsibilities:
                md += f"- {resp}\n"
            md += "\n"
        
        md += "## Data Models\n\n"
        for model in self.content.data_models:
            md += f"### {model.name}\n\n"
            md += f"{model.description}\n\n"
            md += "**Fields:**\n"
            for field, ftype in model.fields.items():
                md += f"- `{field}`: {ftype}\n"
            md += "\n"
        
        md += "## API Endpoints\n\n"
        for endpoint in self.content.api_endpoints:
            md += f"### {endpoint.method} {endpoint.path}\n\n"
            md += f"{endpoint.description}\n\n"
            if endpoint.auth_required:
                md += "*Requires authentication*\n\n"
        
        return md
```

---

## Day 3-4: Message Bus & Communication

**File: `backend/core/communication/message_bus.py`**
```python
from __future__ import annotations
import asyncio
from typing import Dict, List, Optional, Callable
from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4

class Message(BaseModel):
    """Message between agents"""
    msg_id: str = Field(default_factory=lambda: f"msg_{uuid4().hex[:8]}")
    from_agent: str
    to_agent: str
    msg_type: str  # "document", "question", "feedback", "command"
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    requires_response: bool = False
    in_response_to: Optional[str] = None
    
class MessageBus:
    """Pub/sub system for agent communication"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._history: List[Message] = []
        self._response_handlers: Dict[str, asyncio.Future] = {}
        
    async def publish(self, message: Message) -> None:
        """Publish message to subscribers"""
        self._history.append(message)
        
        # Deliver to subscriber
        if message.to_agent in self._subscribers:
            for queue in self._subscribers[message.to_agent]:
                await queue.put(message)
        
        # If this is a response, resolve the waiting future
        if message.in_response_to and message.in_response_to in self._response_handlers:
            future = self._response_handlers[message.in_response_to]
            future.set_result(message)
            del self._response_handlers[message.in_response_to]
    
    def subscribe(self, agent_name: str) -> asyncio.Queue:
        """Agent subscribes to messages"""
        queue = asyncio.Queue()
        if agent_name not in self._subscribers:
            self._subscribers[agent_name] = []
        self._subscribers[agent_name].append(queue)
        return queue
    
    async def request_response(self, message: Message, timeout: int = 30) -> Message:
        """Send message and wait for response"""
        message.requires_response = True
        
        # Create future for response
        future = asyncio.Future()
        self._response_handlers[message.msg_id] = future
        
        # Publish message
        await self.publish(message)
        
        # Wait for response with timeout
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            # Clean up
            if message.msg_id in self._response_handlers:
                del self._response_handlers[message.msg_id]
            raise
    
    def get_conversation(self, between: tuple[str, str]) -> List[Message]:
        """Get conversation between two agents"""
        a1, a2 = between
        return [m for m in self._history 
                if (m.from_agent == a1 and m.to_agent == a2) or
                   (m.from_agent == a2 and m.to_agent == a1)]
    
    def get_all_messages(self, agent: str) -> List[Message]:
        """Get all messages to/from an agent"""
        return [m for m in self._history 
                if m.from_agent == agent or m.to_agent == agent]
```

---

## Day 5-7: Base Agent with Communication

**File: `backend/agents/base_society_agent.py`**
```python
from abc import ABC, abstractmethod
from typing import Protocol, Optional, Dict, Any
import asyncio

from backend.core.communication.message_bus import MessageBus, Message
from backend.core.documents.base import Document, DocumentStore, DocumentType

class SocietyAgent(ABC):
    """Base class for all agents in the society"""
    
    def __init__(self, 
                 name: str,
                 message_bus: MessageBus,
                 document_store: DocumentStore):
        self.name = name
        self.message_bus = message_bus
        self.document_store = document_store
        self._inbox = message_bus.subscribe(name)
        self._running = False
        
    @property
    @abstractmethod
    def role(self) -> str:
        """Agent's role in the society"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """What this agent can do"""
        pass
    
    async def start(self):
        """Start agent's message loop"""
        self._running = True
        asyncio.create_task(self._message_loop())
    
    async def stop(self):
        """Stop agent"""
        self._running = False
    
    async def _message_loop(self):
        """Process incoming messages"""
        while self._running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    self._inbox.get(),
                    timeout=1.0
                )
                
                # Handle message
                response = await self.receive_message(message)
                
                # Send response if message requires one
                if message.requires_response and response:
                    await self.message_bus.publish(response)
                    
            except asyncio.TimeoutError:
                # No message, continue
                continue
            except Exception as e:
                print(f"Error in {self.name} message loop: {e}")
    
    @abstractmethod
    async def receive_message(self, msg: Message) -> Optional[Message]:
        """Handle incoming message - implement in subclass"""
        pass
    
    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Document:
        """Execute agent's main task - implement in subclass"""
        pass
    
    # Helper methods for communication
    
    async def send_document(self, doc: Document, to_agent: str) -> None:
        """Send a document to another agent"""
        message = Message(
            from_agent=self.name,
            to_agent=to_agent,
            msg_type="document",
            payload={"doc_id": doc.doc_id}
        )
        await self.message_bus.publish(message)
    
    async def request_document(self, 
                              doc_type: DocumentType,
                              from_agent: str,
                              run_id: str) -> Optional[Document]:
        """Request a document from another agent"""
        message = Message(
            from_agent=self.name,
            to_agent=from_agent,
            msg_type="request_document",
            payload={
                "doc_type": doc_type.value,
                "run_id": run_id
            }
        )
        
        response = await self.message_bus.request_response(message)
        
        if response and "doc_id" in response.payload:
            return self.document_store.get(response.payload["doc_id"])
        
        return None
    
    async def ask_clarification(self, question: str, to_agent: str) -> str:
        """Ask another agent for clarification"""
        message = Message(
            from_agent=self.name,
            to_agent=to_agent,
            msg_type="question",
            payload={"question": question}
        )
        
        response = await self.message_bus.request_response(message, timeout=60)
        return response.payload.get("answer", "")
    
    async def provide_feedback(self, 
                              doc_id: str,
                              feedback: str,
                              to_agent: str) -> None:
        """Give feedback on a document"""
        message = Message(
            from_agent=self.name,
            to_agent=to_agent,
            msg_type="feedback",
            payload={
                "doc_id": doc_id,
                "feedback": feedback
            }
        )
        await self.message_bus.publish(message)
```

---

## Day 8-10: First Real Agent - Product Manager

**File: `backend/agents/product_manager.py`**
```python
from typing import Dict, Any, Optional, List
from anthropic import AsyncAnthropic

from .base_society_agent import SocietyAgent
from backend.core.documents.prd import PRDDocument, PRDContent, UserStory, SuccessMetric
from backend.core.communication.message_bus import Message

class ProductManagerAgent(SocietyAgent):
    """Creates PRD from user idea"""
    
    role = "Product Manager"
    capabilities = ["create_prd", "refine_requirements", "prioritize_features"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = AsyncAnthropic()
    
    async def receive_message(self, msg: Message) -> Optional[Message]:
        """Handle incoming messages"""
        if msg.msg_type == "question":
            # Someone asking about the PRD
            answer = await self._answer_question(msg.payload["question"])
            return Message(
                from_agent=self.name,
                to_agent=msg.from_agent,
                msg_type="answer",
                payload={"answer": answer},
                in_response_to=msg.msg_id
            )
        
        elif msg.msg_type == "request_document":
            # Someone requesting the PRD
            run_id = msg.payload["run_id"]
            docs = self.document_store.get_by_type(
                DocumentType.PRD,
                run_id=run_id
            )
            if docs:
                return Message(
                    from_agent=self.name,
                    to_agent=msg.from_agent,
                    msg_type="document",
                    payload={"doc_id": docs[0].doc_id},
                    in_response_to=msg.msg_id
                )
        
        return None
    
    async def execute_task(self, task: Dict[str, Any]) -> PRDDocument:
        """Main task: Create PRD from user idea"""
        user_idea = task["user_idea"]
        run_id = task["run_id"]
        
        # Use Claude to analyze idea and create structured PRD
        prompt = f"""
        You are a senior Product Manager. Analyze this project idea and create a comprehensive Product Requirements Document (PRD).
        
        User Idea:
        {user_idea}
        
        Create a structured PRD with:
        1. Project name and description
        2. Target users
        3. At least 3-5 user stories (use proper "As a X, I want Y, so that Z" format)
        4. Success metrics
        5. Technical constraints (if any mentioned)
        6. What's explicitly out of scope
        
        Return your analysis as JSON matching this schema:
        {{
          "project_name": "...",
          "project_description": "...",
          "target_users": ["...", "..."],
          "user_stories": [
            {{
              "id": "US-1",
              "as_a": "...",
              "i_want": "...",
              "so_that": "...",
              "acceptance_criteria": ["...", "..."],
              "priority": 1
            }}
          ],
          "success_metrics": [
            {{
              "metric": "...",
              "target": "...",
              "measurement_method": "..."
            }}
          ],
          "constraints": [],
          "out_of_scope": ["..."],
          "assumptions": ["..."]
        }}
        """
        
        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        import json
        content_text = response.content[0].text
        
        # Extract JSON (handle markdown code blocks)
        if "```json" in content_text:
            content_text = content_text.split("```json")[1].split("```")[0]
        elif "```" in content_text:
            content_text = content_text.split("```")[1].split("```")[0]
        
        prd_data = json.loads(content_text.strip())
        
        # Create PRD document
        prd = PRDDocument(
            run_id=run_id,
            created_by=self.name,
            title=f"PRD: {prd_data['project_name']}",
            content=PRDContent(**prd_data)
        )
        
        # Save to document store
        self.document_store.save(prd)
        
        return prd
    
    async def _answer_question(self, question: str) -> str:
        """Answer questions about the PRD"""
        # In real implementation, retrieve relevant PRD and use it as context
        return "I'd need to check the PRD to answer that properly."
```

---

## Testing Your Implementation

**File: `tests/test_document_system.py`**
```python
import pytest
from backend.core.documents.base import DocumentStore
from backend.core.documents.prd import PRDDocument, PRDContent, UserStory
from backend.core.communication.message_bus import MessageBus, Message
from backend.agents.product_manager import ProductManagerAgent

@pytest.mark.asyncio
async def test_document_creation_and_storage():
    """Test document creation and storage"""
    store = DocumentStore()
    
    prd = PRDDocument(
        run_id="test-run-1",
        created_by="product_manager",
        title="Test PRD",
        content=PRDContent(
            project_name="Test Project",
            project_description="A test project",
            target_users=["developers"],
            user_stories=[
                UserStory(
                    id="US-1",
                    as_a="developer",
                    i_want="to test the system",
                    so_that="I can verify it works",
                    acceptance_criteria=["Test passes"],
                    priority=1
                )
            ],
            success_metrics=[],
            constraints=[]
        )
    )
    
    store.save(prd)
    
    # Retrieve
    retrieved = store.get(prd.doc_id)
    assert retrieved is not None
    assert retrieved.content.project_name == "Test Project"
    
    # Get by type
    prds = store.get_by_type(DocumentType.PRD, run_id="test-run-1")
    assert len(prds) == 1

@pytest.mark.asyncio
async def test_message_bus():
    """Test inter-agent messaging"""
    bus = MessageBus()
    
    # Agent subscribes
    inbox = bus.subscribe("architect")
    
    # Send message
    msg = Message(
        from_agent="product_manager",
        to_agent="architect",
        msg_type="document",
        payload={"doc_id": "doc_123"}
    )
    
    await bus.publish(msg)
    
    # Receive message
    received = await inbox.get()
    assert received.from_agent == "product_manager"
    assert received.payload["doc_id"] == "doc_123"

@pytest.mark.asyncio
async def test_product_manager_agent():
    """Test ProductManager agent"""
    bus = MessageBus()
    store = DocumentStore()
    
    agent = ProductManagerAgent(
        name="product_manager",
        message_bus=bus,
        document_store=store
    )
    
    # Start agent
    await agent.start()
    
    # Execute task
    prd = await agent.execute_task({
        "user_idea": "Build a simple todo list app",
        "run_id": "test-run-2"
    })
    
    assert prd is not None
    assert prd.doc_type == DocumentType.PRD
    assert len(prd.content.user_stories) > 0
    
    # Stop agent
    await agent.stop()
```

---

## Week 1 Deliverables Checklist

- [ ] Document base classes implemented
- [ ] PRD document type created
- [ ] System Design document type created
- [ ] DocumentStore working with save/retrieve
- [ ] MessageBus implemented with pub/sub
- [ ] SocietyAgent base class created
- [ ] ProductManager agent implemented
- [ ] Basic tests passing
- [ ] Markdown rendering works
- [ ] Document versioning works

---

## Next Steps (Week 2)

1. Implement Architect agent (consumes PRD, creates SystemDesign)
2. Implement API Designer agent
3. Implement Project Manager agent (task breakdown)
4. Create simple orchestrator to chain agents
5. Add memory system (ChromaDB integration)

---

## Quick Start Commands

```bash
# Setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest tests/test_document_system.py -v

# Start development server
uvicorn main:app --reload
```

---

## Monitoring Progress

Track these metrics daily:
- [ ] Documents created successfully
- [ ] Messages sent/received
- [ ] Agent response times
- [ ] Test coverage %
- [ ] API endpoints working

Good luck with Week 1! 🚀
