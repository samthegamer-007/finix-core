"""
FINIX — Master Orchestrator
Receives user requests, selects workflows, activates agents,
controls execution, synthesizes final response.
Does NOT specialize in finance. Conducts the system.
"""
from schemas.messages import UserQuery, FinixResponse
from schemas.workflow_state import WorkflowState, WorkflowType, WorkflowStatus
from agents.frank import frank
from utils.logger import get_logger

logger = get_logger("finix")

class Finix:
    def __init__(self):
        logger.info("FINIX orchestrator initialized")

    def handle(self, query: UserQuery) -> FinixResponse:
        """
        Main entry point. Called by the API layer.
        1. Read memory from Frank
        2. Select workflow
        3. Execute workflow
        4. Write result to Frank
        5. Return response
        """
        logger.info(f"FINIX received query | user: {query.user_id} | query: {query.query[:80]}")

        # Step 1: Read context from Frank
        user_context = frank.read_user_context(query.user_id)

        # Step 2: Select workflow
        workflow_type = self._select_workflow(query.query)
        logger.info(f"FINIX selected workflow: {workflow_type}")

        # Step 3: Build workflow state
        state = WorkflowState(
            workflow_type=workflow_type,
            user_id=query.user_id,
            original_query=query.query,
            context=user_context
        )

        # Step 4: Execute
        state.mark_running()
        try:
            state = self._execute_workflow(state, query)
            state.mark_completed()
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            state.mark_failed()
            return FinixResponse(
                status="error",
                query=query.query,
                response={"message": f"FINIX encountered an error: {str(e)}"},
                workflow_used=workflow_type,
                user_id=query.user_id
            )

        # Step 5: Write result to Frank
        if state.final_response:
            frank.write_workflow_result(
                user_id=query.user_id,
                workflow_id=state.workflow_id,
                summary={"query": query.query, "result": state.final_response}
            )

        return FinixResponse(
            status="success",
            query=query.query,
            response=state.final_response or {},
            workflow_used=workflow_type,
            user_id=query.user_id
        )

    def _select_workflow(self, query: str) -> WorkflowType:
        """
        Simple intent-based workflow selector.
        Will be improved with Gemini classification in later phases.
        """
        q = query.lower()
        decision_keywords = ["should i buy", "should i sell", "invest", "worth buying", "good investment", "trade"]
        if any(kw in q for kw in decision_keywords):
            return WorkflowType.DECISION
        return WorkflowType.RESEARCH

    def _execute_workflow(self, state: WorkflowState, query: UserQuery) -> WorkflowState:
        """Routes to the correct workflow module."""
        if state.workflow_type == WorkflowType.RESEARCH:
            from workflows.research import research_workflow
            return research_workflow.run(state)
        elif state.workflow_type == WorkflowType.DECISION:
            # Decision workflow not built yet — fall back to research
            logger.warning("Decision workflow not yet built — falling back to research")
            from workflows.research import research_workflow
            return research_workflow.run(state)
        else:
            raise ValueError(f"Unknown workflow type: {state.workflow_type}")

finix = Finix()
