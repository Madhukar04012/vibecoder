# Models package - all models and enums exported for easy import

# Enums
from backend.models.enums import TaskStatus, TaskPriority, AgentRole

# Core models (original)
from backend.models.user import User
from backend.models.project import Project
from backend.models.project_agent import ProjectAgent
from backend.models.project_plan import ProjectPlan
from backend.models.conversation import Conversation
from backend.models.task import Task
from backend.models.execution_log import ExecutionLog

# MetaGPT-style models (new)
from backend.models.agent import Agent, AgentStatus
from backend.models.agent_message import AgentMessage, MessageType, SenderType
from backend.models.project_run import ProjectRun, RunStatus
from backend.models.artifact import Artifact, ArtifactType
