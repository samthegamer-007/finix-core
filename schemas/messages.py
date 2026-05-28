from dataclasses import dataclass, field
from typing import Any, Optional, Dict
from enum import Enum

class AgentName(str, Enum):
    FINIX = "finix"
    ROME = "rome"
    KOVA = "kova"
    DIMON = "dimon"
    FRANK = "frank"

class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"

@dataclass
class UserQuery:
    query: str
    user_id: str = "default_user"
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FinixResponse:
    status: str
    query: str
    response: Dict[str, Any]
    workflow_used: str
    user_id: str

    def to_dict(self):
        return {
            "status": self.status,
            "query": self.query,
            "response": self.response,
            "workflow_used": self.workflow_used,
            "user_id": self.user_id
        }
