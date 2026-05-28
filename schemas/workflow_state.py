from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List
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

@dataclass
class WorkflowState:
    workflow_type: WorkflowType
    user_id: str
    original_query: str
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: WorkflowStatus = WorkflowStatus.PENDING
    active_agents: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    final_response: Optional[Dict] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None

    def mark_running(self):
        self.status = WorkflowStatus.RUNNING

    def mark_completed(self):
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.utcnow().isoformat()

    def mark_failed(self):
        self.status = WorkflowStatus.FAILED
        self.completed_at = datetime.utcnow().isoformat()
