"""
Multi-Project Orchestrator - Scale to 100s of projects (Phase 3.3)

Manages multiple concurrent projects with:
- Semaphore-based concurrency control
- Project status tracking
- Resource management
- Queue management for high load
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from backend.core.orchestration.society_orchestrator import SocietyOrchestrator

logger = logging.getLogger("multi_project_orchestrator")


class ProjectStatus(str, Enum):
    """Status of a project execution."""
    QUEUED = "queued"           # Waiting to start
    RUNNING = "running"         # Currently executing
    COMPLETED = "completed"     # Successfully finished
    FAILED = "failed"          # Execution failed
    CANCELLED = "cancelled"    # Manually cancelled
    TIMEOUT = "timeout"        # Exceeded time limit


@dataclass
class Project:
    """Represents a project being executed."""
    project_id: str
    user_idea: str
    status: ProjectStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0  # 0.0 - 100.0
    current_agent: Optional[str] = None
    documents_created: List[str] = field(default_factory=list)
    cost_usd: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "user_idea": self.user_idea[:100] + "..." if len(self.user_idea) > 100 else self.user_idea,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "current_agent": self.current_agent,
            "documents_count": len(self.documents_created),
            "cost_usd": round(self.cost_usd, 4),
            "error": self.error,
        }


class MultiProjectOrchestrator:
    """
    Orchestrates multiple concurrent projects.
    
    Features:
    - Concurrency control (max N projects at once)
    - Project queue management
    - Status tracking and reporting
    - Resource monitoring
    - Automatic cleanup
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        max_queue_size: int = 100,
        default_timeout: int = 600,  # 10 minutes
    ):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.default_timeout = default_timeout
        
        # Concurrency control
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        # Project storage
        self._projects: Dict[str, Project] = {}
        self._project_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._running_tasks: Dict[str, asyncio.Task] = {}
        
        # Statistics
        self._total_completed = 0
        self._total_failed = 0
        self._total_cost = 0.0
        
        # Background task
        self._queue_processor: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the orchestrator and queue processor."""
        if self._running:
            return
        
        self._running = True
        self._queue_processor = asyncio.create_task(self._process_queue())
        logger.info("MultiProjectOrchestrator started (max_concurrent=%d)", self.max_concurrent)

    async def stop(self) -> None:
        """Stop the orchestrator gracefully."""
        self._running = False
        
        # Cancel running projects
        for task in self._running_tasks.values():
            task.cancel()
        
        if self._queue_processor:
            self._queue_processor.cancel()
            try:
                await self._queue_processor
            except asyncio.CancelledError:
                pass
        
        logger.info("MultiProjectOrchestrator stopped")

    async def submit_project(
        self,
        user_idea: str,
        project_id: Optional[str] = None,
        template: Optional[str] = None,
        priority: int = 0,  # Higher = more priority
    ) -> str:
        """
        Submit a new project for execution.
        
        Args:
            user_idea: The project description
            project_id: Optional custom project ID
            template: Optional template to use
            priority: Priority level (higher = executed sooner)
            
        Returns:
            project_id: The ID of the submitted project
        """
        project_id = project_id or f"proj_{uuid4().hex[:10]}"
        
        if project_id in self._projects:
            raise ValueError(f"Project {project_id} already exists")

        # Create project
        project = Project(
            project_id=project_id,
            user_idea=user_idea,
            status=ProjectStatus.QUEUED,
            created_at=datetime.now(timezone.utc),
        )
        
        self._projects[project_id] = project
        
        # Add to queue with priority
        try:
            await self._project_queue.put((priority, project_id, {
                "user_idea": user_idea,
                "template": template,
            }))
            logger.info("Project %s submitted (queue position: %d)", 
                       project_id, self._project_queue.qsize())
        except asyncio.QueueFull:
            project.status = ProjectStatus.FAILED
            project.error = "Queue full - too many pending projects"
            raise RuntimeError("Project queue is full")
        
        return project_id

    async def _process_queue(self) -> None:
        """Background task to process the project queue."""
        while self._running:
            try:
                # Wait for a project
                priority, project_id, config = await self._project_queue.get()
                
                # Execute with semaphore (concurrency control)
                task = asyncio.create_task(
                    self._execute_project(project_id, config)
                )
                self._running_tasks[project_id] = task
                
                # Clean up when done
                task.add_done_callback(
                    lambda t, pid=project_id: self._cleanup_task(pid, t)
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error processing queue: %s", e)
                await asyncio.sleep(1)

    async def _execute_project(
        self,
        project_id: str,
        config: Dict[str, Any],
    ) -> None:
        """Execute a single project."""
        async with self._semaphore:
            project = self._projects.get(project_id)
            if not project:
                return
            
            # Update status
            project.status = ProjectStatus.RUNNING
            project.started_at = datetime.now(timezone.utc)
            
            logger.info("Starting project %s", project_id)
            
            try:
                # Create orchestrator for this project
                orchestrator = SocietyOrchestrator()
                
                # Set up progress tracking (must be async — orchestrator awaits callbacks)
                async def on_event(agent: str, event: str, payload: Dict[str, Any]) -> None:
                    project.current_agent = agent
                    if event == "completed":
                        project.progress = min(100.0, project.progress + 12.5)

                orchestrator.on_event(on_event)
                
                # Execute workflow
                result = await asyncio.wait_for(
                    orchestrator.execute_workflow(
                        user_idea=config["user_idea"],
                        run_id=project_id,
                        template=config.get("template"),
                    ),
                    timeout=self.default_timeout,
                )
                
                # Update project
                project.status = ProjectStatus.COMPLETED
                project.result = result
                project.documents_created = [d.doc_id for d in result.get("documents", [])]
                
                # Calculate cost
                metrics = result.get("metrics", {})
                project.cost_usd = metrics.get("total_cost", 0.0)
                
                self._total_completed += 1
                self._total_cost += project.cost_usd
                
                logger.info("Project %s completed (cost: $%.4f)", 
                           project_id, project.cost_usd)
                
            except asyncio.TimeoutError:
                project.status = ProjectStatus.TIMEOUT
                project.error = f"Exceeded timeout of {self.default_timeout}s"
                self._total_failed += 1
                logger.warning("Project %s timed out", project_id)
                
            except Exception as e:
                project.status = ProjectStatus.FAILED
                project.error = str(e)
                self._total_failed += 1
                logger.exception("Project %s failed: %s", project_id, e)
            
            finally:
                project.completed_at = datetime.now(timezone.utc)
                project.progress = 100.0 if project.status == ProjectStatus.COMPLETED else project.progress

    def _cleanup_task(self, project_id: str, task: asyncio.Task) -> None:
        """Clean up completed task."""
        if project_id in self._running_tasks:
            del self._running_tasks[project_id]

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        return self._projects.get(project_id)

    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project status."""
        project = self._projects.get(project_id)
        return project.to_dict() if project else None

    def list_projects(
        self,
        status: Optional[ProjectStatus] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List projects with optional filtering."""
        projects = list(self._projects.values())
        
        if status:
            projects = [p for p in projects if p.status == status]
        
        # Sort by creation date (newest first)
        projects.sort(key=lambda p: p.created_at, reverse=True)
        
        return [p.to_dict() for p in projects[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        active = sum(1 for p in self._projects.values() if p.status == ProjectStatus.RUNNING)
        queued = self._project_queue.qsize()
        
        return {
            "total_projects": len(self._projects),
            "active_projects": active,
            "queued_projects": queued,
            "completed": self._total_completed,
            "failed": self._total_failed,
            "total_cost_usd": round(self._total_cost, 4),
            "max_concurrent": self.max_concurrent,
            "capacity_used": f"{active}/{self.max_concurrent}",
        }

    async def cancel_project(self, project_id: str) -> bool:
        """Cancel a running or queued project."""
        project = self._projects.get(project_id)
        if not project:
            return False
        
        if project.status == ProjectStatus.QUEUED:
            # Remove from queue (note: this is a simplification)
            project.status = ProjectStatus.CANCELLED
            return True
        
        if project.status == ProjectStatus.RUNNING:
            # Cancel the task
            task = self._running_tasks.get(project_id)
            if task:
                task.cancel()
                project.status = ProjectStatus.CANCELLED
                return True
        
        return False

    def get_health(self) -> Dict[str, Any]:
        """Get orchestrator health status."""
        queue_full = self._project_queue.qsize() >= self.max_queue_size * 0.9
        capacity_full = len(self._running_tasks) >= self.max_concurrent
        
        status = "healthy"
        if queue_full and capacity_full:
            status = "overloaded"
        elif queue_full:
            status = "busy"
        elif capacity_full:
            status = "at_capacity"
        
        return {
            "status": status,
            "running": self._running,
            "queue_utilization": f"{self._project_queue.qsize()}/{self.max_queue_size}",
            "concurrency_utilization": f"{len(self._running_tasks)}/{self.max_concurrent}",
        }


# Global orchestrator instance
_orchestrator: Optional[MultiProjectOrchestrator] = None


async def get_multi_project_orchestrator() -> MultiProjectOrchestrator:
    """Get or create the global multi-project orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiProjectOrchestrator()
        await _orchestrator.start()
    return _orchestrator
