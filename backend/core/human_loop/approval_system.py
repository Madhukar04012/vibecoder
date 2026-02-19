"""Human-in-the-loop approval points (plan Phase 3.3)."""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"

class Approval(BaseModel):
    checkpoint_id: str
    status: ApprovalStatus
    feedback: str = ""
    approved_by: Optional[str] = None

class ApprovalSystem:
    APPROVAL_POINTS = ["after_prd", "after_design", "before_deployment"]

    def __init__(self) -> None:
        self._pending: Dict[str, Approval] = {}
        self._decisions: Dict[str, Approval] = {}

    def request_approval(self, checkpoint: str, artifact_id: str, metadata: Dict[str, Any] = None) -> str:
        key = f"{checkpoint}:{artifact_id}"
        self._pending[key] = Approval(checkpoint_id=checkpoint, status=ApprovalStatus.PENDING)
        return key

    def approve(self, key: str, approved_by: str = "user") -> Approval:
        a = self._pending.get(key, Approval(checkpoint_id="", status=ApprovalStatus.PENDING))
        a = Approval(checkpoint_id=a.checkpoint_id, status=ApprovalStatus.APPROVED, approved_by=approved_by)
        self._decisions[key] = a
        self._pending.pop(key, None)
        return a

    def reject(self, key: str, feedback: str, rejected_by: str = "user") -> Approval:
        a = self._pending.get(key, Approval(checkpoint_id="", status=ApprovalStatus.PENDING))
        a = Approval(checkpoint_id=a.checkpoint_id, status=ApprovalStatus.REJECTED, feedback=feedback, approved_by=rejected_by)
        self._decisions[key] = a
        self._pending.pop(key, None)
        return a

    def get_pending(self) -> List[str]:
        return list(self._pending.keys())

    def get_approval(self, key: str) -> Optional[Approval]:
        return self._decisions.get(key)
