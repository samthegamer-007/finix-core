from pydantic import BaseModel, Field
from typing import Any, Optional
from enum import Enum
import uuid
from datetime import datetime

class WorkflowType(str, Enum):
    RESEARCH = "research"
    DECISION = "decision"
    QUICK_RESPONSE = "quick_response"
    MEMORY_OP = "memory_op"

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowState(BaseModel):
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_type: WorkflowType
    status: WorkflowStatus = WorkflowStatus.PENDING
    user_id: str
    original_query: str
    active_agents: list[str] = []
    context: dict[str, Any] = {}       # memory injected by Frank before workflow
    results: dict[str, Any] = {}       # accumulated agent results
    final_response: Optional[dict] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None

    def mark_running(self):
        self.status = WorkflowStatus.RUNNING

    def mark_completed(self):
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.utcnow().isoformat()

    def mark_failed(self):
        self.status = WorkflowStatus.FAILED
        self.completed_at = datetime.utcnow().isoformat()
