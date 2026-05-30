import requests
from config import config
from utils.logger import get_logger

logger = get_logger("search_service")

TAVILY_API_URL = "https://api.tavily.com/search"

class SearchService:

    def search(self, query: str, max_results: int = 5,
               days_back: int = 7, search_depth: str = "basic") -> dict:
        logger.debug(f"Search | query: {query[:60]} | days_back: {days_back}")
        if config.TAVILY_API_KEY:
            result = self._tavily_search(query, max_results, days_back, search_depth)
            if result and not result.get("error"):
                return result
        logger.warning("Tavily unavailable — falling back to DuckDuckGo")
        return self._ddg_search(query, max_results)

    def _tavily_search(self, query: str, max_results: int,
                       days_back: int, search_depth: str) -> dict:
        try:
            payload = {
                "api_key": config.TAVILY_API_KEY,
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results + 3,
                "days": days_back,
                "include_answer": False,
                "include_raw_content": False,
                "include_domains": [],
                "exclude_domains": config.EXCLUDED_SOURCES
            }
            resp = requests.post(TAVILY_API_URL, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            filtered = self._filter_and_rank(results)
            return {
                "source": "tavily",
                "query": query,
                "count": len(filtered[:max_results]),
                "results": filtered[:max_results]
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("Tavily quota exhausted — falling back")
                return {"error": "quota_exhausted"}
            logger.error(f"Tavily HTTP error: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return {"error": str(e)}

    def _ddg_search(self, query: str, max_results: int) -> dict:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; FINIX-AI/1.0)"}
            params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
            resp = requests.get(
                "https://api.duckduckgo.com/",
                params=params,
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(item, dict) and item.get("Text"):
                    url = item.get("FirstURL", "")
                    if any(ex in url for ex in config.EXCLUDED_SOURCES):
                        continue
                    results.append({
                        "title": item.get("Text", "")[:100],
                        "url": url,
                        "source": self._extract_domain(url),
                        "published_date": None,
                        "content": item.get("Text", ""),
                        "score": 0.5
                    })
            return {
                "source": "duckduckgo",
                "query": query,
                "count": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return {"error": str(e), "results": []}

    def _filter_and_rank(self, results: list) -> list:
        filtered = []
        for r in results:
            url = r.get("url", "")
            if any(ex in url for ex in config.EXCLUDED_SOURCES):
                continue
            is_preferred = any(ps in url for ps in config.PREFERRED_SOURCES)
            r["preferred_source"] = is_preferred
            r["source"] = self._extract_domain(url)
            filtered.append(r)
        filtered.sort(key=lambda x: (
            -int(x.get("preferred_source", False)),
            -float(x.get("score", 0))
        ))
        return filtered

    def _extract_domain(self, url: str) -> str:
        try:
            domain = url.split("//")[-1].split("/")[0]
            return domain.replace("www.", "")
        except Exception:
            return url

search_service = SearchService()
