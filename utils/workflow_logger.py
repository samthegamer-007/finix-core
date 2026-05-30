from utils.logger import get_logger
from datetime import datetime

logger = get_logger("workflow_logger")

class WorkflowLogger:
    def __init__(self):
        self._logs = {}

    def start_workflow(self, workflow_id: str, user_id: str, query: str, workflow_type: str):
        self._logs[workflow_id] = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "query": query,
            "workflow_type": workflow_type,
            "started_at": datetime.utcnow().isoformat(),
            "events": []
        }

    def log_event(self, workflow_id: str, agent: str, event_type: str, data: dict):
        if workflow_id not in self._logs:
            return
        self._logs[workflow_id]["events"].append({
            "agent": agent,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        })

    def complete_workflow(self, workflow_id: str, status: str):
        if workflow_id not in self._logs:
            return
        self._logs[workflow_id]["completed_at"] = datetime.utcnow().isoformat()
        self._logs[workflow_id]["status"] = status

    def get_workflow_trace(self, workflow_id: str) -> dict:
        return self._logs.get(workflow_id, {"error": "Workflow not found"})

    def get_recent_traces(self, limit: int = 10) -> list:
        traces = list(self._logs.values())
        return sorted(traces, key=lambda x: x.get("started_at", ""), reverse=True)[:limit]

workflow_logger = WorkflowLogger()
