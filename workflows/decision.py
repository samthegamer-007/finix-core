"""
DECISION WORKFLOW — Stub
Will activate: FINIX + ROME + KOVA + DIMON
Not built yet. Placeholder.
"""
from schemas.workflow_state import WorkflowState
from utils.logger import get_logger

logger = get_logger("workflow.decision")

class DecisionWorkflow:
    def run(self, state: WorkflowState) -> WorkflowState:
        raise NotImplementedError("Decision workflow not yet built. Coming in a later phase.")

decision_workflow = DecisionWorkflow()
