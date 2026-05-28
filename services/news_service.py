"""
News service used exclusively by Rome.
Fetches financial news via NewsAPI.
"""
import requests
from config import config
from utils.logger import get_logger

logger = get_logger("news_service")

NEWSAPI_BASE = "https://newsapi.org/v2"

class NewsService:
    def get_news(self, query: str, limit: int = 5) -> dict:
        """Fetch top financial news articles for a given query."""
        if not config.NEWS_API_KEY:
            logger.warning("NEWS_API_KEY not set — skipping news fetch")
            return {"articles": [], "warning": "News API key not configured"}

        try:
            url = f"{NEWSAPI_BASE}/everything"
            params = {
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": limit,
                "apiKey": config.NEWS_API_KEY
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            articles = [
                {
                    "title": a.get("title", ""),
                    "source": a.get("source", {}).get("name", ""),
                    "published_at": a.get("publishedAt", ""),
                    "description": a.get("description", ""),
                    "url": a.get("url", "")
                }
                for a in data.get("articles", [])[:limit]
            ]

            return {"query": query, "count": len(articles), "articles": articles}

        except Exception as e:
            logger.error(f"News fetch error | query: {query} | {e}")
            return {"error": str(e), "query": query}

news_service = NewsService()
