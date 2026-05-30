from utils.logger import get_logger

logger = get_logger("ranking_processor")

class RankingProcessor:

    def rank_by_return(self, assets: list, key: str = "period_return_pct", top_n: int = 20) -> list:
        try:
            valid = [a for a in assets if not a.get("error") and a.get("metrics", {}).get(key) is not None]
            ranked = sorted(valid, key=lambda x: x["metrics"].get(key, 0), reverse=True)
            for i, asset in enumerate(ranked):
                asset["rank"] = i + 1
            return ranked[:top_n]
        except Exception as e:
            logger.error(f"Ranking error: {e}")
            return []

    def rank_worst(self, assets: list, key: str = "period_return_pct", bottom_n: int = 10) -> list:
        try:
            valid = [a for a in assets if not a.get("error") and a.get("metrics", {}).get(key) is not None]
            ranked = sorted(valid, key=lambda x: x["metrics"].get(key, 0), reverse=False)
            for i, asset in enumerate(ranked):
                asset["rank"] = i + 1
            return ranked[:bottom_n]
        except Exception as e:
            logger.error(f"Worst ranking error: {e}")
            return []

    def filter_by_sector(self, assets: list, sector: str) -> list:
        return [a for a in assets if a.get("sector", "").lower() == sector.lower()]

    def filter_by_cap_tier(self, assets: list, tier: str) -> list:
        return [a for a in assets if a.get("metrics", {}).get("market_cap_tier") == tier]

    def summarize_rankings(self, ranked: list, metric: str = "period_return_pct") -> dict:
        if not ranked:
            return {"error": "No ranked data"}
        values = [a["metrics"].get(metric, 0) for a in ranked]
        return {
            "total_assets_ranked": len(ranked),
            "metric_used": metric,
            "top_performer": {
                "name": ranked[0].get("name") or ranked[0].get("ticker") or ranked[0].get("scheme_name"),
                "value": ranked[0]["metrics"].get(metric)
            },
            "worst_performer": {
                "name": ranked[-1].get("name") or ranked[-1].get("ticker") or ranked[-1].get("scheme_name"),
                "value": ranked[-1]["metrics"].get(metric)
            },
            "average_value": round(sum(values) / len(values), 2),
            "positive_count": sum(1 for v in values if v > 0),
            "negative_count": sum(1 for v in values if v < 0),
            "rankings": [
                {
                    "rank": a.get("rank"),
                    "name": a.get("name") or a.get("ticker") or a.get("scheme_name"),
                    "ticker": a.get("ticker") or a.get("scheme_code"),
                    metric: a["metrics"].get(metric)
                }
                for a in ranked
            ]
        }

ranking_processor = RankingProcessor()
