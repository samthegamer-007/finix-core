"""
KOVA — Market Intelligence Agent
Interprets Rome's raw data into meaningful financial signals.
Handles: sentiment, trends, macro context, preliminary risk.
Cold, clinical, precise. Does not fetch — always uses Rome.
"""
from utils.logger import get_logger
import json

logger = get_logger("kova")

class Kova:
    def __init__(self):
        logger.info("Kova initialized")

    def build_analysis_prompt(self, processed_data: dict, query: str) -> str:
        data_str = json.dumps(processed_data, indent=2)[:3000]
        prompt = f"""You are KOVA, market intelligence layer inside FINIX AI.

User query: "{query}"

Pre-processed structured data:
{data_str}

Your responsibilities:
1. TREND: Identify dominant market trend from quantitative evidence
2. SENTIMENT: Assess market sentiment from performance metrics and news facts
3. NARRATIVES: Identify key market narratives visible in the data
4. RISKS: Flag specific risk signals from the metrics
5. CONTEXT: Provide relevant macro or sector context

CRITICAL RULES:
- Reason from evidence to conclusion. Never from source to conclusion.
- WRONG: "Reuters reports inflation is falling therefore inflation is falling"
- RIGHT: "CPI data shows inflation declined from X% to Y% in the latest reading"
- Cite specific numbers from the data. Do not invent figures.
- Do not perform calculations — numbers are pre-computed.
- Do not rank assets — rankings are pre-computed.
- Never mention source names as justification for a conclusion.
- Be analytical, concise, institutional in tone.
- Max 250 words. Clean prose. No headers."""
        return prompt

    def parse_response(self, raw_response) -> dict:
        if isinstance(raw_response, dict):
            text = str(raw_response)
        else:
            text = str(raw_response).strip() if raw_response else "No analysis available"
        return {"agent": "kova", "intelligence_brief": text}

kova = Kova()
