"""
ROME — API Broker & Tool Executor
The only agent allowed to touch external APIs.
Does NOT reason. Does NOT analyze. Returns structured data only.
Named after Roman Roy (Succession) — executes, doesn't overthink.
"""
import json
import time
from utils.logger import get_logger
from services.gemini_service import gemini_service

logger = get_logger("rome")

class Rome:
    def __init__(self):
        logger.info("Rome initialized")

    def fetch(self, task: dict) -> dict:
        task_type = task.get("type")
        params = task.get("params", {})
        logger.debug(f"Rome fetch | type: {task_type} | params: {params}")
        try:
            handlers = {
                "stock": self._fetch_stock,
                "stock_history": self._fetch_stock_history,
                "bulk_stock_history": self._fetch_bulk_stock_history,
                "nifty500_weekly": self._fetch_nifty500_weekly,
                "mutual_fund_nav": self._fetch_mutual_fund_nav,
                "mutual_funds_performance": self._fetch_mutual_funds_performance,
                "crypto": self._fetch_crypto,
                "index": self._fetch_index,
                "index_history": self._fetch_index_history,
                "news": self._fetch_news,
                "web_search": self._fetch_web_search,
            }
            handler = handlers.get(task_type)
            if not handler:
                return {"error": f"Unknown task type: {task_type}"}
            return handler(params)
        except Exception as e:
            logger.error(f"Rome fetch error | type: {task_type} | {e}")
            return {"error": str(e), "task_type": task_type}

    def interpret_query(self, query: str, context: dict = {}) -> list:
        logger.debug(f"Rome interpreting query: {query[:80]}")

        prompt = f"""You are ROME, financial data retrieval engine inside FINIX AI.

Your job: Determine what data must be fetched to answer this query.
You decide information requirements. You do NOT analyze or conclude.

Available fetch types:

TIER 1 — Structured APIs (use first):
- stock: single stock current. params: {{"ticker": "AAPL"}}
- stock_history: single stock historical. params: {{"ticker": "AAPL", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}}
- bulk_stock_history: multiple stocks historical. params: {{"tickers": ["AAPL"], "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}}
- nifty500_weekly: Indian stocks bulk historical. params: {{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "limit": 100}}
- mutual_funds_performance: Indian MFs in date range. params: {{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}}
- mutual_fund_nav: single MF NAV. params: {{"scheme_code": "119528"}}
- crypto: single crypto. params: {{"coin_id": "bitcoin"}}
- index: market index current. params: {{"index_symbol": "^NSEI"}}
- index_history: index historical. params: {{"index_symbol": "^NSEI", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}}

TIER 2 — News API:
- news: financial news. params: {{"query": "search term", "limit": 5}}

TIER 3 — Web search (only when Tier 1+2 insufficient):
- web_search: params: {{"query": "search term", "max_results": 5, "days_back": 7}}
  Use for: geopolitical events, policy announcements, earnings transcripts,
  global macro, European/Asian markets, central bank statements, regulatory filings.
  Target primary sources with site: operators.
  Example: "Nvidia export restrictions site:reuters.com OR site:ft.com"

User query: "{query}"
Today's date: {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d')}

Think about ALL information angles:
- What market data is needed?
- What news context is needed?
- What macro/geopolitical context is needed?
- What primary sources should be checked?

Respond ONLY with valid JSON array. No explanation. No markdown. Raw JSON only.
Example: [{{"type": "stock", "params": {{"ticker": "NVDA"}}}}, {{"type": "news", "params": {{"query": "Nvidia", "limit": 5}}}}]

Rules:
- Indian market screening → nifty500_weekly + mutual_funds_performance
- Single stock → stock + stock_history + news
- Complex geopolitical query → news + web_search with site: operators
- Crypto → crypto + news
- Always fetch news alongside market data
- Use web_search sparingly"""

        try:
            raw = gemini_service.call(prompt)
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1]
                clean = clean.rsplit("```", 1)[0]
            tasks = json.loads(clean)
            logger.info(f"Rome interpreted {len(tasks)} fetch tasks: {[t['type'] for t in tasks]}")
            return tasks if isinstance(tasks, list) else []
        except Exception as e:
            logger.error(f"Rome interpretation failed: {e}")
            return []

    def fetch_all(self, tasks: list) -> dict:
        results = {}
        for i, task in enumerate(tasks):
            task_type = task.get("type", f"task_{i}")
            result = self.fetch(task)
            key = f"{task_type}_{i}" if task_type in results else task_type
            results[key] = result
            logger.debug(f"Rome fetched: {key}")
        return results

    def _fetch_stock(self, params: dict) -> dict:
        from services.market_service import market_service
        ticker = params.get("ticker", "")
        if not ticker:
            return {"error": "No ticker provided"}
        time.sleep(1)
        result = market_service.get_stock_data(ticker)
        if result.get("error"):
            logger.warning(f"Stock fetch failed for {ticker} — escalating to web search")
            return self._fetch_web_search({
                "query": f"{ticker} stock price current data site:reuters.com OR site:marketwatch.com OR site:cnbc.com",
                "max_results": 3,
                "days_back": 1
            })
        return result

    def _fetch_stock_history(self, params: dict) -> dict:
        from services.market_service import market_service
        ticker = params.get("ticker", "")
        start = params.get("start", "")
        end = params.get("end", "")
        if not all([ticker, start, end]):
            return {"error": "ticker, start, end required"}
        time.sleep(1)
        result = market_service.get_stock_history(ticker, start, end)
        if result.get("error"):
            logger.warning(f"Stock history failed for {ticker} — escalating to web search")
            return self._fetch_web_search({
                "query": f"{ticker} stock performance {start} to {end} site:reuters.com OR site:marketwatch.com",
                "max_results": 3,
                "days_back": 30
            })
        return result

    def _fetch_bulk_stock_history(self, params: dict) -> dict:
        from services.market_service import market_service
        tickers = params.get("tickers", [])
        start = params.get("start", "")
        end = params.get("end", "")
        if not all([tickers, start, end]):
            return {"error": "tickers, start, end required"}
        time.sleep(1)
        return market_service.get_bulk_stock_history(tickers, start, end)

    def _fetch_nifty500_weekly(self, params: dict) -> dict:
        from services.market_service import market_service
        start = params.get("start", "")
        end = params.get("end", "")
        limit = params.get("limit", 100)
        if not all([start, end]):
            return {"error": "start and end required"}
        time.sleep(1)
        return market_service.get_nifty500_weekly_data(start, end, limit)

    def _fetch_mutual_fund_nav(self, params: dict) -> dict:
        from services.market_service import market_service
        scheme_code = params.get("scheme_code", "")
        if not scheme_code:
            return {"error": "scheme_code required"}
        return market_service.get_mutual_fund_nav(scheme_code)

    def _fetch_mutual_funds_performance(self, params: dict) -> dict:
        from services.market_service import market_service
        start = params.get("start", "")
        end = params.get("end", "")
        if not all([start, end]):
            return {"error": "start and end required"}
        return market_service.get_top_mutual_funds_performance(start, end)

    def _fetch_crypto(self, params: dict) -> dict:
        from services.market_service import market_service
        coin_id = params.get("coin_id", "")
        if not coin_id:
            return {"error": "coin_id required"}
        return market_service.get_crypto_data(coin_id)

    def _fetch_index(self, params: dict) -> dict:
        from services.market_service import market_service
        symbol = params.get("index_symbol", "")
        if not symbol:
            return {"error": "index_symbol required"}
        time.sleep(1)
        return market_service.get_index_data(symbol)

    def _fetch_index_history(self, params: dict) -> dict:
        from services.market_service import market_service
        symbol = params.get("index_symbol", "")
        start = params.get("start", "")
        end = params.get("end", "")
        if not all([symbol, start, end]):
            return {"error": "index_symbol, start, end required"}
        time.sleep(1)
        return market_service.get_index_history(symbol, start, end)

    def _fetch_news(self, params: dict) -> dict:
        from services.news_service import news_service
        query = params.get("query", "")
        limit = params.get("limit", 5)
        if not query:
            return {"error": "query required"}
        return news_service.get_news(query, limit)

    def _fetch_web_search(self, params: dict) -> dict:
        from services.search_service import search_service
        query = params.get("query", "")
        max_results = params.get("max_results", 5)
        days_back = params.get("days_back", 7)
        if not query:
            return {"error": "query required"}
        return search_service.search(query, max_results, days_back)

rome = Rome()
