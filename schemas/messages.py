from pydantic import BaseModel
from typing import Any, Optional
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

class AgentMessage(BaseModel):
    sender: AgentName
    receiver: AgentName
    message_type: MessageType
    payload: dict[str, Any]
    workflow_id: Optional[str] = None

class UserQuery(BaseModel):
    query: str
    user_id: Optional[str] = "default_user"
    context: Optional[dict[str, Any]] = {}

class FinixResponse(BaseModel):
    status: str
    query: str
    response: dict[str, Any]
    workflow_used: str
    user_id: str
