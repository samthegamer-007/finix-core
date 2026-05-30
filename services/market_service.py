"""
Market data service used exclusively by Rome.
Fetches stock and crypto data via yfinance and CoinGecko.
"""
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger("market_service")

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
MFAPI_BASE = "https://api.mfapi.in/mf"

NIFTY500_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS",
    "BAJFINANCE.NS", "WIPRO.NS", "ULTRACEMCO.NS", "NESTLEIND.NS", "POWERGRID.NS",
    "NTPC.NS", "ONGC.NS", "TECHM.NS", "HCLTECH.NS", "SUNPHARMA.NS",
    "DRREDDY.NS", "DIVISLAB.NS", "CIPLA.NS", "APOLLOHOSP.NS", "BAJAJFINSV.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "ADANIGREEN.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "TATACONSUM.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "COALINDIA.NS",
    "BPCL.NS", "IOC.NS", "GAIL.NS", "INDUSINDBK.NS", "EICHERMOT.NS",
    "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "BRITANNIA.NS", "DABUR.NS", "MARICO.NS",
    "GODREJCP.NS", "COLPAL.NS", "PIDILITIND.NS", "BERGEPAINT.NS", "HAVELLS.NS",
    "VOLTAS.NS", "SIEMENS.NS", "ABB.NS", "BOSCHLTD.NS", "CUMMINSIND.NS",
    "PAGEIND.NS", "TRENT.NS", "NYKAA.NS", "DMART.NS", "ZOMATO.NS",
    "NAUKRI.NS", "INDIGO.NS", "IRCTC.NS", "CONCOR.NS", "DLF.NS",
    "GODREJPROP.NS", "OBEROIRLTY.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS",
    "UNIONBANK.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS", "BANDHANBNK.NS", "CHOLAFIN.NS",
    "MUTHOOTFIN.NS", "LICHSGFIN.NS", "RECLTD.NS", "PFC.NS", "IRFC.NS",
    "NHPC.NS", "SJVN.NS", "TATAPOWER.NS", "ADANIPOWER.NS", "TORNTPOWER.NS",
    "AUROPHARMA.NS", "LUPIN.NS", "BIOCON.NS", "ALKEM.NS", "TORNTPHARM.NS",
    "MPHASIS.NS", "LTIM.NS", "PERSISTENT.NS", "COFORGE.NS", "KPITTECH.NS"
]

TOP_MF_SCHEMES = {
    "119528": "ABSL Large Cap Fund - Direct Growth",
    "120503": "HDFC Top 100 Fund - Direct Growth",
    "125354": "ICICI Pru Bluechip Fund - Direct Growth",
    "120716": "SBI Bluechip Fund - Direct Growth",
    "118989": "HDFC Mid-Cap Opportunities - Direct Growth",
    "125307": "PGIM India Midcap - Direct Growth",
    "118825": "Axis Midcap Fund - Direct Growth",
    "120505": "HDFC Small Cap Fund - Direct Growth",
    "125494": "Nippon India Small Cap - Direct Growth",
    "118778": "SBI Small Cap Fund - Direct Growth",
    "120594": "HDFC Flexi Cap Fund - Direct Growth",
    "118834": "Axis Flexi Cap Fund - Direct Growth",
    "122639": "Mirae Asset Large Cap - Direct Growth",
}

class MarketService:

    def get_stock_data(self, ticker: str) -> dict:
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
                "currency": info.get("currency", "USD"),
                "summary": (info.get("longBusinessSummary", "") or "")[:300]
            }
        except Exception as e:
            logger.error(f"Stock fetch error | {ticker} | {e}")
            return {"error": str(e), "ticker": ticker}

    def get_stock_history(self, ticker: str, start: str, end: str) -> dict:
        try:
            data = yf.download(ticker.upper(), start=start, end=end, progress=False)
            if data.empty:
                return {"error": f"No data for {ticker} in range {start} to {end}"}
            history = []
            for date, row in data.iterrows():
                close = row.get("Close")
                if hasattr(close, 'item'):
                    close = close.item()
                history.append({
                    "date": str(date.date()),
                    "close": round(float(close), 4) if close else None,
                    "volume": int(row.get("Volume", 0))
                })
            return {
                "ticker": ticker.upper(),
                "start": start,
                "end": end,
                "data_points": len(history),
                "history": history
            }
        except Exception as e:
            logger.error(f"Stock history error | {ticker} | {e}")
            return {"error": str(e), "ticker": ticker}

    def get_bulk_stock_history(self, tickers: list, start: str, end: str) -> dict:
        try:
            ticker_str = " ".join(tickers)
            data = yf.download(ticker_str, start=start, end=end, progress=False)
            if data.empty:
                return {"error": "No data returned for bulk fetch"}
            results = {}
            close_data = data["Close"] if "Close" in data.columns else data
            for ticker in tickers:
                try:
                    if ticker in close_data.columns:
                        series = close_data[ticker].dropna()
                        if len(series) >= 2:
                            history = [
                                {"date": str(d.date()), "close": round(float(v), 4)}
                                for d, v in series.items()
                            ]
                            results[ticker] = {
                                "ticker": ticker,
                                "history": history,
                                "data_points": len(history)
                            }
                except Exception as e:
                    logger.warning(f"Bulk fetch skip | {ticker} | {e}")
                    continue
            logger.info(f"Bulk fetch complete | {len(results)}/{len(tickers)} tickers")
            return {"results": results, "fetched": len(results), "requested": len(tickers)}
        except Exception as e:
            logger.error(f"Bulk stock history error: {e}")
            return {"error": str(e)}

    def get_nifty500_weekly_data(self, start: str, end: str, limit: int = 100) -> dict:
        tickers = NIFTY500_TICKERS[:limit]
        logger.info(f"Fetching Nifty500 | {len(tickers)} tickers | {start} to {end}")
        return self.get_bulk_stock_history(tickers, start, end)

    def get_index_data(self, index_symbol: str) -> dict:
        return self.get_stock_data(index_symbol)

    def get_index_history(self, index_symbol: str, start: str, end: str) -> dict:
        return self.get_stock_history(index_symbol, start, end)

    def get_mutual_fund_nav(self, scheme_code: str) -> dict:
        try:
            url = f"{MFAPI_BASE}/{scheme_code}"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            meta = data.get("meta", {})
            nav_data = data.get("data", [])
            return {
                "scheme_code": scheme_code,
                "scheme_name": meta.get("scheme_name", ""),
                "fund_house": meta.get("fund_house", ""),
                "scheme_type": meta.get("scheme_type", ""),
                "scheme_category": meta.get("scheme_category", ""),
                "latest_nav": float(nav_data[0]["nav"]) if nav_data else None,
                "nav_date": nav_data[0]["date"] if nav_data else None,
                "historical_nav": nav_data[:30]
            }
        except Exception as e:
            logger.error(f"MF NAV fetch error | {scheme_code} | {e}")
            return {"error": str(e), "scheme_code": scheme_code}

    def get_top_mutual_funds_performance(self, start: str, end: str) -> dict:
        results = {}
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        for scheme_code, scheme_name in TOP_MF_SCHEMES.items():
            try:
                url = f"{MFAPI_BASE}/{scheme_code}"
                resp = requests.get(url, timeout=10)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                nav_data = data.get("data", [])
                period_navs = []
                for entry in nav_data:
                    try:
                        entry_date = datetime.strptime(entry["date"], "%d-%m-%Y")
                        if start_dt <= entry_date <= end_dt:
                            period_navs.append({
                                "date": entry_date.strftime("%Y-%m-%d"),
                                "nav": float(entry["nav"])
                            })
                    except Exception:
                        continue
                if len(period_navs) >= 2:
                    period_navs.sort(key=lambda x: x["date"])
                    results[scheme_code] = {
                        "scheme_code": scheme_code,
                        "scheme_name": scheme_name,
                        "fund_house": data.get("meta", {}).get("fund_house", ""),
                        "category": data.get("meta", {}).get("scheme_category", ""),
                        "nav_history": period_navs,
                        "start_nav": period_navs[0]["nav"],
                        "end_nav": period_navs[-1]["nav"],
                        "data_points": len(period_navs)
                    }
            except Exception as e:
                logger.warning(f"MF fetch skip | {scheme_code} | {e}")
                continue
        logger.info(f"MF performance fetch complete | {len(results)} funds")
        return {"results": results, "fetched": len(results)}

    def get_crypto_data(self, coin_id: str) -> dict:
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
            logger.error(f"Crypto fetch error | {coin_id} | {e}")
            return {"error": str(e), "coin_id": coin_id}

market_service = MarketService()
