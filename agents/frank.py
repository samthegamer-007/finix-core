"""
FRANK — Persistent Memory Subsystem
Not a reasoning agent. Acts as a structured memory service.
Only FINIX communicates with Frank.
"""
from utils.logger import get_logger

logger = get_logger("frank")

class Frank:
    def __init__(self):
        # Supabase client wired in Phase 7
        # For now Frank uses in-memory dict as placeholder
        self._store: dict = {}
        logger.info("Frank initialized (in-memory mode — Supabase wired in Phase 7)")

    def read_user_context(self, user_id: str) -> dict:
        """Read stored context for a user/agent before a workflow."""
        context = self._store.get(user_id, {
            "user_id": user_id,
            "preferences": {},
            "watchlist": [],
            "recent_insights": []
        })
        logger.debug(f"Frank read context for user: {user_id}")
        return context

    def write_workflow_result(self, user_id: str, workflow_id: str, summary: dict):
        """Write summarized workflow result after completion."""
        if user_id not in self._store:
            self._store[user_id] = {
                "user_id": user_id,
                "preferences": {},
                "watchlist": [],
                "recent_insights": []
            }
        self._store[user_id]["recent_insights"].append({
            "workflow_id": workflow_id,
            "summary": summary
        })
        # Keep only last 10 insights in memory
        self._store[user_id]["recent_insights"] = \
            self._store[user_id]["recent_insights"][-10:]
        logger.debug(f"Frank wrote workflow result for user: {user_id} | workflow: {workflow_id}")

    def update_preferences(self, user_id: str, preferences: dict):
        if user_id not in self._store:
            self._store[user_id] = {"user_id": user_id, "preferences": {}, "watchlist": [], "recent_insights": []}
        self._store[user_id]["preferences"].update(preferences)
        logger.debug(f"Frank updated preferences for: {user_id}")

    def update_watchlist(self, user_id: str, add: list = [], remove: list = []):
        if user_id not in self._store:
            self._store[user_id] = {"user_id": user_id, "preferences": {}, "watchlist": [], "recent_insights": []}
        current = set(self._store[user_id]["watchlist"])
        current.update(add)
        current.difference_update(remove)
        self._store[user_id]["watchlist"] = list(current)
        logger.debug(f"Frank updated watchlist for: {user_id}")

frank = Frank()
