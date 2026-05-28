"""
Market data service used exclusively by Rome.
Fetches stock and crypto data via yfinance and CoinGecko.
"""
import yfinance as yf
import requests
from utils.logger import get_logger

logger = get_logger("market_service")

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

class MarketService:
    def get_stock_data(self, ticker: str) -> dict:
        """Fetch key stock info via yfinance."""
        try:
            stock = yf.Ticker(ticker.upper())
            info = stock.info

            return {
                "ticker": ticker.upper(),
                "name": info.get("longName", ""),
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "previous_close": info.get("previousClose"),
                "day_high": info.get("dayHigh"),
                "day_low": info.get("dayLow"),
                "volume": info.get("volume"),
                "market_cap": info.get("marketCap"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "pe_ratio": info.get("trailingPE"),
                "sector": info.get("sector", ""),
                "summary": info.get("longBusinessSummary", "")[:300] if info.get("longBusinessSummary") else ""
            }
        except Exception as e:
            logger.error(f"Stock fetch error | ticker: {ticker} | {e}")
            return {"error": str(e), "ticker": ticker}

    def get_crypto_data(self, coin_id: str) -> dict:
        """Fetch crypto data via CoinGecko (free, no key needed)."""
        try:
            url = f"{COINGECKO_BASE}/simple/price"
            params = {
                "ids": coin_id.lower(),
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true"
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json().get(coin_id.lower(), {})

            return {
                "coin_id": coin_id,
                "price_usd": data.get("usd"),
                "market_cap_usd": data.get("usd_market_cap"),
                "volume_24h_usd": data.get("usd_24h_vol"),
                "change_24h_pct": data.get("usd_24h_change")
            }
        except Exception as e:
            logger.error(f"Crypto fetch error | coin: {coin_id} | {e}")
            return {"error": str(e), "coin_id": coin_id}

market_service = MarketService()
