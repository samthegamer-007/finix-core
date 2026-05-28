"""
KOVA — Market Intelligence Agent
Interprets Rome's raw data into meaningful financial signals.
Handles: sentiment, trends, macro context, preliminary risk.
Cold, clinical, precise. Does not fetch — always uses Rome.
"""
from utils.logger import get_logger

logger = get_logger("kova")

class Kova:
    def __init__(self):
        logger.info("Kova initialized")

    def build_analysis_prompt(self, raw_data: dict, query: str) -> str:
        """
        Builds Kova's question for the Gemini broker call.
        Does not call Gemini itself — returns the prompt string.
        FINIX bundles this with other agent prompts into one broker call.
        """
        stock = raw_data.get("stock", {})
        news = raw_data.get("news", {})
        crypto = raw_data.get("crypto", {})

        data_summary = ""
        if stock and not stock.get("error"):
            data_summary += f"STOCK DATA: {stock}\n"
        if crypto and not crypto.get("error"):
            data_summary += f"CRYPTO DATA: {crypto}\n"
        if news and not news.get("error"):
            articles = news.get("articles", [])[:5]
            headlines = [a.get("title", "") for a in articles]
            data_summary += f"RECENT NEWS HEADLINES: {headlines}\n"

        prompt = f"""You are KOVA, a market intelligence analyst inside the FINIX AI system.
User query: "{query}"

Raw market data provided:
{data_summary}

Your job:
1. Identify the key market trend (bullish/bearish/neutral) with brief reasoning
2. Summarize the most relevant news sentiment (1-2 sentences)
3. Flag any notable risks or macro signals visible in the data
4. Prepare a concise intelligence brief for the financial reasoning layer

Be precise. Be structured. No fluff. Return your analysis as clean prose under 200 words."""

        return prompt

    def parse_response(self, raw_response: str) -> dict:
        """Parses Kova's section of the broker response into structured output."""
        return {
            "agent": "kova",
            "intelligence_brief": raw_response.strip()
        }

kova = Kova()
