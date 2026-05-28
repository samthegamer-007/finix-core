"""
ROME — API Broker & Tool Executor
The only agent allowed to touch external APIs.
Does NOT reason. Does NOT analyze. Returns structured data only.
Named after Roman Roy (Succession) — executes, doesn't overthink.
"""
from utils.logger import get_logger

logger = get_logger("rome")

class Rome:
    def __init__(self):
        logger.info("Rome initialized (services wired in Phase 3)")

    def fetch(self, task: dict) -> dict:
        """
        Receives a structured fetch instruction from FINIX or KOVA.
        task = { "type": "stock" | "news" | "crypto", "params": { ... } }
        Returns structured JSON. Never raises to caller — returns error dict instead.
        """
        task_type = task.get("type")
        params = task.get("params", {})

        logger.debug(f"Rome fetch | type: {task_type} | params: {params}")

        try:
            if task_type == "stock":
                return self._fetch_stock(params)
            elif task_type == "news":
                return self._fetch_news(params)
            elif task_type == "crypto":
                return self._fetch_crypto(params)
            else:
                return {"error": f"Unknown task type: {task_type}"}
        except Exception as e:
            logger.error(f"Rome fetch error | type: {task_type} | {e}")
            return {"error": str(e), "task_type": task_type}

    def _fetch_stock(self, params: dict) -> dict:
        # Wired in Phase 3 via market_service
        from services.market_service import market_service
        ticker = params.get("ticker", "")
        if not ticker:
            return {"error": "No ticker provided"}
        return market_service.get_stock_data(ticker)

    def _fetch_news(self, params: dict) -> dict:
        # Wired in Phase 3 via news_service
        from services.news_service import news_service
        query = params.get("query", "")
        limit = params.get("limit", 5)
        if not query:
            return {"error": "No query provided"}
        return news_service.get_news(query, limit)

    def _fetch_crypto(self, params: dict) -> dict:
        # Wired in Phase 3 via market_service
        from services.market_service import market_service
        coin_id = params.get("coin_id", "")
        if not coin_id:
            return {"error": "No coin_id provided"}
        return market_service.get_crypto_data(coin_id)

rome = Rome()
