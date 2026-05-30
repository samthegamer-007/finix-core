from schemas.messages import UserQuery, FinixResponse
from schemas.workflow_state import WorkflowState, WorkflowType
from agents.frank import frank
from services.gemini_service import gemini_service
from utils.logger import get_logger

logger = get_logger("finix")

class Finix:
    def __init__(self):
        logger.info("FINIX orchestrator initialized")

    def handle(self, query: UserQuery) -> dict:
        logger.info(f"FINIX received query | user: {query.user_id}")

        user_context = frank.read_user_context(query.user_id)
        workflow_type = self._select_workflow(query.query)
        logger.info(f"FINIX selected workflow: {workflow_type}")

        state = WorkflowState(
            workflow_type=workflow_type,
            user_id=query.user_id,
            original_query=query.query,
            context=user_context
        )

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
                workflow_used=workflow_type.value,
                user_id=query.user_id
            ).to_dict()

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
            workflow_used=workflow_type.value,
            user_id=query.user_id
        ).to_dict()

    def _select_workflow(self, query: str) -> WorkflowType:
        prompt = f"""You are FINIX, a financial intelligence orchestrator.
Classify this user query into exactly one workflow type.

RESEARCH: queries asking for information, analysis, news, market data, trends, explanations, comparisons, historical performance
DECISION: queries explicitly asking what to DO — buy, sell, invest, allocate, recommend an action

User query: "{query}"

Respond with exactly one word: RESEARCH or DECISION"""

        try:
            result = gemini_service.call(prompt).strip().upper()
            if "DECISION" in result:
                logger.info("FINIX classified workflow: DECISION")
                return WorkflowType.DECISION
            logger.info("FINIX classified workflow: RESEARCH")
            return WorkflowType.RESEARCH
        except Exception as e:
            logger.warning(f"Workflow classification failed, defaulting to RESEARCH: {e}")
            return WorkflowType.RESEARCH

    def _execute_workflow(self, state: WorkflowState, query: UserQuery) -> WorkflowState:
        if state.workflow_type in (WorkflowType.RESEARCH, WorkflowType.DECISION):
            from workflows.research import research_workflow
            return research_workflow.run(state)
        raise ValueError(f"Unknown workflow type: {state.workflow_type}")

finix = Finix()
