from utils.logger import get_logger
import statistics

logger = get_logger("market_processor")

class MarketProcessor:

    def process_stock(self, raw: dict) -> dict:
        if raw.get("error"):
            return {"error": raw["error"], "ticker": raw.get("ticker")}
        try:
            price = raw.get("price") or 0
            prev_close = raw.get("previous_close") or 0
            week_high = raw.get("52_week_high") or 0
            week_low = raw.get("52_week_low") or 0
            day_high = raw.get("day_high") or 0
            day_low = raw.get("day_low") or 0
            market_cap = raw.get("market_cap") or 0
            volume = raw.get("volume") or 0
            daily_return_pct = round(((price - prev_close) / prev_close * 100) if prev_close else 0, 2)
            week_range = week_high - week_low
            week_position_pct = round(((price - week_low) / week_range * 100) if week_range else 0, 2)
            day_range = round(day_high - day_low, 4) if day_high and day_low else 0
            pct_from_52w_high = round(((price - week_high) / week_high * 100) if week_high else 0, 2)
            pct_from_52w_low = round(((price - week_low) / week_low * 100) if week_low else 0, 2)
            return {
                "ticker": raw.get("ticker"),
                "name": raw.get("name"),
                "sector": raw.get("sector"),
                "price": price,
                "currency": raw.get("currency", "USD"),
                "metrics": {
                    "daily_return_pct": daily_return_pct,
                    "day_high": day_high,
                    "day_low": day_low,
                    "day_range": day_range,
                    "volume": volume,
                    "market_cap": market_cap,
                    "market_cap_tier": self._classify_market_cap(market_cap),
                    "pe_ratio": raw.get("pe_ratio"),
                    "52w_high": week_high,
                    "52w_low": week_low,
                    "52w_position_pct": week_position_pct,
                    "pct_from_52w_high": pct_from_52w_high,
                    "pct_from_52w_low": pct_from_52w_low,
                },
                "raw_summary": raw.get("summary", "")
            }
        except Exception as e:
            logger.error(f"Stock processing error: {e}")
            return {"error": str(e), "ticker": raw.get("ticker")}

    def process_crypto(self, raw: dict) -> dict:
        if raw.get("error"):
            return {"error": raw["error"], "coin_id": raw.get("coin_id")}
        try:
            price = raw.get("price_usd") or 0
            change_24h = raw.get("change_24h_pct") or 0
            market_cap = raw.get("market_cap_usd") or 0
            volume = raw.get("volume_24h_usd") or 0
            vol_to_mcap = round((volume / market_cap * 100) if market_cap else 0, 4)
            return {
                "coin_id": raw.get("coin_id"),
                "price_usd": price,
                "metrics": {
                    "change_24h_pct": round(change_24h, 2),
                    "market_cap_usd": market_cap,
                    "volume_24h_usd": volume,
                    "volume_to_mcap_pct": vol_to_mcap,
                    "momentum_signal": self._classify_momentum(change_24h),
                }
            }
        except Exception as e:
            logger.error(f"Crypto processing error: {e}")
            return {"error": str(e)}

    def process_historical(self, history: list) -> dict:
        if not history or len(history) < 2:
            return {"error": "Insufficient historical data"}
        try:
            closes = [h["close"] for h in history if h.get("close")]
            dates = [h["date"] for h in history if h.get("close")]
            if len(closes) < 2:
                return {"error": "Insufficient price data"}
            start_price = closes[0]
            end_price = closes[-1]
            period_return_pct = round((end_price - start_price) / start_price * 100, 2)
            daily_returns = [
                (closes[i] - closes[i-1]) / closes[i-1] * 100
                for i in range(1, len(closes))
            ]
            volatility = round(statistics.stdev(daily_returns), 4) if len(daily_returns) > 1 else 0
            sma_7 = round(statistics.mean(closes[-7:]), 4) if len(closes) >= 7 else None
            sma_20 = round(statistics.mean(closes[-20:]), 4) if len(closes) >= 20 else None
            sma_50 = round(statistics.mean(closes[-50:]), 4) if len(closes) >= 50 else None
            return {
                "period": f"{dates[0]} to {dates[-1]}",
                "data_points": len(closes),
                "metrics": {
                    "start_price": start_price,
                    "end_price": end_price,
                    "period_return_pct": period_return_pct,
                    "period_high": max(closes),
                    "period_low": min(closes),
                    "volatility_pct": volatility,
                    "sma_7": sma_7,
                    "sma_20": sma_20,
                    "sma_50": sma_50,
                    "trend_signal": self._classify_trend(period_return_pct, volatility),
                }
            }
        except Exception as e:
            logger.error(f"Historical processing error: {e}")
            return {"error": str(e)}

    def _classify_market_cap(self, market_cap):
        if not market_cap: return "unknown"
        if market_cap >= 200_000_000_000: return "mega_cap"
        if market_cap >= 10_000_000_000: return "large_cap"
        if market_cap >= 2_000_000_000: return "mid_cap"
        if market_cap >= 300_000_000: return "small_cap"
        return "micro_cap"

    def _classify_momentum(self, change_24h):
        if change_24h >= 5: return "strong_bullish"
        if change_24h >= 2: return "bullish"
        if change_24h >= -2: return "neutral"
        if change_24h >= -5: return "bearish"
        return "strong_bearish"

    def _classify_trend(self, return_pct, volatility):
        if return_pct >= 5 and volatility < 3: return "strong_uptrend"
        if return_pct >= 2: return "uptrend"
        if return_pct <= -5 and volatility < 3: return "strong_downtrend"
        if return_pct <= -2: return "downtrend"
        return "sideways"

market_processor = MarketProcessor()
