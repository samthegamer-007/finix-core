from utils.logger import get_logger
import statistics

logger = get_logger("risk_processor")

class RiskProcessor:

    def compute_risk_profile(self, processed_stock: dict, historical: dict = None) -> dict:
        try:
            metrics = processed_stock.get("metrics", {})
            risk_signals = []
            risk_score = 0
            week_pos = metrics.get("52w_position_pct", 50)
            if week_pos >= 90:
                risk_signals.append("trading_near_52w_high")
                risk_score += 20
            elif week_pos <= 10:
                risk_signals.append("trading_near_52w_low")
                risk_score += 15
            pe = metrics.get("pe_ratio")
            if pe and pe > 50:
                risk_signals.append("high_pe_ratio")
                risk_score += 15
            elif pe and pe < 0:
                risk_signals.append("negative_earnings")
                risk_score += 25
            daily_return = abs(metrics.get("daily_return_pct", 0))
            if daily_return > 5:
                risk_signals.append("high_daily_volatility")
                risk_score += 20
            elif daily_return > 3:
                risk_signals.append("elevated_daily_move")
                risk_score += 10
            if historical and not historical.get("error"):
                vol = historical.get("metrics", {}).get("volatility_pct", 0)
                if vol > 5:
                    risk_signals.append("high_historical_volatility")
                    risk_score += 20
                elif vol > 2:
                    risk_signals.append("moderate_volatility")
                    risk_score += 10
            cap_tier = metrics.get("market_cap_tier", "unknown")
            if cap_tier in ["micro_cap", "small_cap"]:
                risk_signals.append("small_cap_risk")
                risk_score += 15
            return {
                "risk_score": min(risk_score, 100),
                "risk_level": self._classify_risk(risk_score),
                "risk_signals": risk_signals,
                "signal_count": len(risk_signals)
            }
        except Exception as e:
            logger.error(f"Risk computation error: {e}")
            return {"error": str(e)}

    def compute_portfolio_risk(self, assets: list) -> dict:
        try:
            if not assets:
                return {"error": "No assets provided"}
            returns = [a.get("metrics", {}).get("daily_return_pct", 0) for a in assets if not a.get("error")]
            if not returns:
                return {"error": "No valid return data"}
            avg_return = round(statistics.mean(returns), 2)
            return_std = round(statistics.stdev(returns), 2) if len(returns) > 1 else 0
            positive = sum(1 for r in returns if r > 0)
            negative = sum(1 for r in returns if r < 0)
            return {
                "portfolio_size": len(returns),
                "avg_daily_return_pct": avg_return,
                "return_std_dev": return_std,
                "positive_assets": positive,
                "negative_assets": negative,
                "breadth_pct": round(positive / len(returns) * 100, 1),
                "portfolio_risk_level": self._classify_risk(return_std * 10)
            }
        except Exception as e:
            logger.error(f"Portfolio risk error: {e}")
            return {"error": str(e)}

    def _classify_risk(self, score: float) -> str:
        if score >= 70: return "high"
        if score >= 40: return "medium"
        return "low"

risk_processor = RiskProcessor()
