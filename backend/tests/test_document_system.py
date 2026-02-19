"""
Tests for document-driven architecture (plan Week 1).

Covers DocumentStore, MessageBus, PRD/SystemDesign documents, and Society Product Manager.
"""

import pytest
from backend.core.documents.base import (
    DocumentStore,
    DocumentType,
    Document,
    DocumentVersion,
)
from backend.core.documents.prd import (
    PRDDocument,
    PRDContent,
    UserStory,
    SuccessMetric,
    TechConstraint,
)
from backend.core.documents.system_design import (
    SystemDesignDocument,
    SystemDesignContent,
    Component,
    DataModel,
    APIEndpoint,
)
from backend.core.communication.message_bus import MessageBus, Message


# --- Document creation and storage ---


def test_document_store_save_and_get() -> None:
    """DocumentStore saves and retrieves documents by id."""
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
                    priority=1,
                )
            ],
            success_metrics=[
                SuccessMetric(
                    metric="Quality",
                    target="All tests pass",
                    measurement_method="pytest",
                )
            ],
            constraints=[],
        ),
    )
    store.save(prd)
    retrieved = store.get(prd.doc_id)
    assert retrieved is not None
    assert retrieved.content.project_name == "Test Project"
    assert len(retrieved.content.user_stories) == 1
    assert retrieved.content.user_stories[0].id == "US-1"


def test_document_store_get_by_type_and_run() -> None:
    """DocumentStore indexes by type and run_id."""
    store = DocumentStore()
    prd = PRDDocument(
        run_id="run-a",
        created_by="product_manager",
        title="PRD A",
        content=PRDContent(
            project_name="Project A",
            project_description="Desc",
            target_users=["u"],
            user_stories=[
                UserStory(
                    id="US-1",
                    as_a="u",
                    i_want="x",
                    so_that="y",
                    acceptance_criteria=["z"],
                    priority=1,
                )
            ],
            success_metrics=[],
            constraints=[],
        ),
    )
    store.save(prd)
    by_type = store.get_by_type(DocumentType.PRD, run_id="run-a")
    assert len(by_type) == 1
    assert by_type[0].doc_id == prd.doc_id
    by_run = store.get_by_run("run-a")
    assert len(by_run) == 1


def test_prd_to_markdown() -> None:
    """PRD renders to markdown."""
    prd = PRDDocument(
        run_id="r1",
        created_by="pm",
        title="My PRD",
        content=PRDContent(
            project_name="My App",
            project_description="An app",
            target_users=["users"],
            user_stories=[
                UserStory(
                    id="US-1",
                    as_a="user",
                    i_want="feature",
                    so_that="benefit",
                    acceptance_criteria=["AC1"],
                    priority=1,
                )
            ],
            success_metrics=[],
            constraints=[],
        ),
    )
    md = prd.to_markdown()
    assert "My App" in md
    assert "US-1" in md
    assert "user" in md and "feature" in md


def test_document_versioning() -> None:
    """Document create_new_version produces a new version."""
    prd = PRDDocument(
        run_id="r1",
        created_by="pm",
        title="V1",
        content=PRDContent(
            project_name="P",
            project_description="D",
            target_users=["u"],
            user_stories=[
                UserStory(
                    id="US-1",
                    as_a="u",
                    i_want="x",
                    so_that="y",
                    acceptance_criteria=["z"],
                    priority=1,
                )
            ],
            success_metrics=[],
            constraints=[],
        ),
    )
    v2 = prd.create_new_version(changes="Updated", updated_by="architect")
    assert v2.version == 2
    assert v2.doc_id != prd.doc_id
    assert len(v2.version_history) == 1
    assert v2.version_history[0].version_number == 1


# --- Message bus ---


@pytest.mark.asyncio
async def test_message_bus_publish_and_subscribe() -> None:
    """MessageBus delivers messages to subscribers."""
    bus = MessageBus()
    inbox = bus.subscribe("architect")
    msg = Message(
        from_agent="product_manager",
        to_agent="architect",
        msg_type="document",
        payload={"doc_id": "doc_123"},
    )
    await bus.publish(msg)
    received = await inbox.get()
    assert received.from_agent == "product_manager"
    assert received.payload["doc_id"] == "doc_123"


@pytest.mark.asyncio
async def test_message_bus_conversation_history() -> None:
    """MessageBus keeps conversation history."""
    bus = MessageBus()
    await bus.publish(
        Message(
            from_agent="pm",
            to_agent="architect",
            msg_type="document",
            payload={"doc_id": "d1"},
        )
    )
    await bus.publish(
        Message(
            from_agent="architect",
            to_agent="pm",
            msg_type="feedback",
            payload={"doc_id": "d1", "feedback": "Looks good"},
        )
    )
    conv = bus.get_conversation(("pm", "architect"))
    assert len(conv) == 2
    all_pm = bus.get_all_messages("pm")
    assert len(all_pm) == 2


@pytest.mark.asyncio
async def test_message_bus_request_response() -> None:
    """MessageBus request_response waits for response."""
    import asyncio
    bus = MessageBus()

    async def responder() -> None:
        inbox = bus.subscribe("architect")
        msg = await inbox.get()
        if msg.msg_type == "request_document":
            await bus.publish(
                Message(
                    from_agent="architect",
                    to_agent=msg.from_agent,
                    msg_type="document",
                    payload={"doc_id": "doc_456"},
                    in_response_to=msg.msg_id,
                )
            )

    asyncio.create_task(responder())
    await asyncio.sleep(0.05)  # let subscriber be ready
    req = Message(
        from_agent="engineer",
        to_agent="architect",
        msg_type="request_document",
        payload={"doc_type": "system_design", "run_id": "r1"},
    )
    response = await bus.request_response(req, timeout=5.0)
    assert response.payload.get("doc_id") == "doc_456"


# --- Society Product Manager (unit test without LLM) ---


@pytest.mark.asyncio
async def test_society_product_manager_receive_request_document() -> None:
    """Society Product Manager responds to request_document with stored PRD."""
    from backend.core.communication.message_bus import MessageBus
    from backend.core.documents.base import DocumentStore, DocumentType
    from backend.core.documents.prd import PRDDocument, PRDContent, UserStory, SuccessMetric
    from backend.agents.society_product_manager import SocietyProductManagerAgent

    bus = MessageBus()
    store = DocumentStore()
    prd = PRDDocument(
        run_id="test-run-req",
        created_by="product_manager",
        title="Stored PRD",
        content=PRDContent(
            project_name="Stored Project",
            project_description="Stored desc",
            target_users=["u"],
            user_stories=[
                UserStory(
                    id="US-1",
                    as_a="u",
                    i_want="x",
                    so_that="y",
                    acceptance_criteria=["z"],
                    priority=1,
                )
            ],
            success_metrics=[],
            constraints=[],
        ),
    )
    store.save(prd)
    agent = SocietyProductManagerAgent(
        name="product_manager",
        message_bus=bus,
        document_store=store,
    )
    msg = Message(
        from_agent="architect",
        to_agent="product_manager",
        msg_type="request_document",
        payload={"doc_type": "product_requirements", "run_id": "test-run-req"},
    )
    response = await agent.receive_message(msg)
    assert response is not None
    assert response.msg_type == "document"
    assert response.payload["doc_id"] == prd.doc_id


@pytest.mark.asyncio
async def test_society_product_manager_receive_question() -> None:
    """Society Product Manager responds to question with answer."""
    from backend.core.communication.message_bus import MessageBus
    from backend.core.documents.base import DocumentStore
    from backend.agents.society_product_manager import SocietyProductManagerAgent

    bus = MessageBus()
    store = DocumentStore()
    agent = SocietyProductManagerAgent(
        name="product_manager",
        message_bus=bus,
        document_store=store,
    )
    msg = Message(
        from_agent="architect",
        to_agent="product_manager",
        msg_type="question",
        payload={"question": "What is the priority of US-1?"},
    )
    response = await agent.receive_message(msg)
    assert response is not None
    assert response.msg_type == "answer"
    assert "answer" in response.payload
