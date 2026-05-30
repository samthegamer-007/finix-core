"""
FRANK — Persistent Memory Subsystem
Not a reasoning agent. Acts as a structured memory service.
Only FINIX communicates with Frank.
"""

from utils.logger import get_logger
from memory.supabase_client import supabase_client
import uuid

logger = get_logger("frank")

class Frank:
    def __init__(self):
        self.db = supabase_client.get()
        logger.info("Frank initialized with Supabase")

    def read_user_context(self, user_id: str) -> dict:
        try:
            result = self.db.table("users").select(
                "user_id, preferences, watchlist"
            ).eq("user_id", user_id).execute()
            if result.data:
                user = result.data[0]
                insights = self._get_recent_insights(user_id)
                return {
                    "user_id": user_id,
                    "preferences": user.get("preferences", {}),
                    "watchlist": user.get("watchlist", []),
                    "recent_insights": insights
                }
            return {"user_id": user_id, "preferences": {}, "watchlist": [], "recent_insights": []}
        except Exception as e:
            logger.error(f"Frank read error: {e}")
            return {"user_id": user_id, "preferences": {}, "watchlist": [], "recent_insights": []}

    def _get_recent_insights(self, user_id: str) -> list:
        try:
            result = self.db.table("insights").select(
                "summary, created_at"
            ).eq("user_id", user_id).order(
                "created_at", desc=True
            ).limit(5).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Frank insights read error: {e}")
            return []

    def write_workflow_result(self, user_id: str, workflow_id: str, summary: dict):
        try:
            self.db.table("workflow_history").insert({
                "user_id": user_id,
                "workflow_id": workflow_id,
                "query": summary.get("query", ""),
                "result": summary.get("result", {})
            }).execute()
            self.db.table("insights").insert({
                "user_id": user_id,
                "workflow_id": workflow_id,
                "summary": summary
            }).execute()
            logger.debug(f"Frank wrote workflow result for: {user_id}")
        except Exception as e:
            logger.error(f"Frank write error: {e}")

    def update_preferences(self, user_id: str, preferences: dict):
        try:
            self.db.table("users").update({
                "preferences": preferences
            }).eq("user_id", user_id).execute()
            logger.debug(f"Frank updated preferences for: {user_id}")
        except Exception as e:
            logger.error(f"Frank preferences update error: {e}")

    def update_watchlist(self, user_id: str, add: list = [], remove: list = []):
        try:
            result = self.db.table("users").select(
                "watchlist"
            ).eq("user_id", user_id).execute()
            current = set(result.data[0].get("watchlist", []) if result.data else [])
            current.update(add)
            current.difference_update(remove)
            self.db.table("users").update({
                "watchlist": list(current)
            }).eq("user_id", user_id).execute()
            logger.debug(f"Frank updated watchlist for: {user_id}")
        except Exception as e:
            logger.error(f"Frank watchlist update error: {e}")

frank = Frank()
