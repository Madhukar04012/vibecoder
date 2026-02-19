"""
Execution Log Model - Audit trail for task executions.
Records what happened, when, by which agent, and the result.
Enhanced with run_id and agent_id for MetaGPT-style tracking.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Core references
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String, nullable=False, index=True)
    
    # MetaGPT-style: Link to run and agent
    run_id = Column(Integer, ForeignKey("project_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    
    agent = Column(String, nullable=False)  # backend_engineer, frontend_engineer, etc.
    status = Column(String, nullable=False)  # success | failure
    
    message = Column(Text, nullable=True)  # Description of what happened
    files_created = Column(Integer, default=0)
    output_dir = Column(String, nullable=True)  # Path to generated files
    
    # Execution timing
    duration_ms = Column(Integer, nullable=True)  # How long the task took
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", backref="execution_logs")
    run = relationship("ProjectRun", back_populates="logs")
    
    def __repr__(self) -> str:
        return f"<ExecutionLog id={self.id} task_id={self.task_id} status={self.status}>"
