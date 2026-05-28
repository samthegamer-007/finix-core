"""
RESEARCH WORKFLOW
Active agents: FINIX + ROME + KOVA
Flow: FINIX → ROME (fetch) → KOVA (analyze via broker) → FINIX (synthesize)
Rome and Kova may communicate directly within this workflow scope.
"""
import re
from agents.rome import rome
from agents.kova import kova
from services.gemini_service import gemini_service
from schemas.workflow_state import WorkflowState
from utils.logger import get_logger

logger = get_logger("workflow.research")

class ResearchWorkflow:
    def run(self, state: WorkflowState) -> WorkflowState:
        state.active_agents = ["finix", "rome", "kova"]
        query = state.original_query
        logger.info(f"Research workflow started | id: {state.workflow_id}")

        # Step 1: FINIX instructs Rome on what to fetch
        fetch_tasks = self._determine_fetch_tasks(query)
        logger.debug(f"Fetch tasks determined: {[t['type'] for t in fetch_tasks]}")

        # Step 2: Rome fetches all data
        raw_data = {}
        for task in fetch_tasks:
            result = rome.fetch(task)
            raw_data[task["type"]] = result
            logger.debug(f"Rome fetched: {task['type']}")

        state.results["raw_data"] = raw_data

        # Step 3: Broker call — Kova analyzes, FINIX synthesizes — ONE Gemini call
        kova_prompt = kova.build_analysis_prompt(raw_data, query)

        finix_prompt = f"""You are FINIX, a financial intelligence orchestrator.
User query: "{query}"

A market intelligence brief will be provided to you from KOVA.
Your job: Write a clear, helpful, beginner-friendly final response.
- Explain what the data means in plain English
- Highlight the most important insight
- Be direct, warm, and honest
- Always end with: "This is not financial advice."
- Keep response under 250 words."""

        broker_results = gemini_service.broker_call({
            "kova": kova_prompt,
            "finix": finix_prompt + f"\n\nKOVA's brief will be: (see kova response in this same batch)"
        })

        # Parse results
        kova_result = kova.parse_response(broker_results.get("kova", "No analysis available"))
        finix_synthesis = broker_results.get("finix", "")

        # If finix synthesis is thin, do a second focused call with kova's output
        if not finix_synthesis or len(finix_synthesis) < 50:
            finix_synthesis = gemini_service.call(
                prompt=f"""User asked: "{query}"
KOVA's market analysis: {kova_result['intelligence_brief']}

Write a clear, beginner-friendly response under 250 words. End with "This is not financial advice." """,
            )

        state.results["kova"] = kova_result
        state.results["finix_synthesis"] = finix_synthesis

        # Step 4: Build final response
        state.final_response = {
            "summary": finix_synthesis,
            "intelligence_brief": kova_result["intelligence_brief"],
            "raw_data_used": list(raw_data.keys()),
            "disclaimer": "This is not financial advice. For informational purposes only."
        }

        logger.info(f"Research workflow completed | id: {state.workflow_id}")
        return state

    def _determine_fetch_tasks(self, query: str) -> list[dict]:
        """
        Parses the query to determine what Rome should fetch.
        Simple keyword-based extraction. Will improve with Gemini classification later.
        """
        tasks = []
        q = query.upper()

        # Known crypto coin IDs (CoinGecko format)
        crypto_map = {
            "BTC": "bitcoin", "BITCOIN": "bitcoin",
            "ETH": "ethereum", "ETHEREUM": "ethereum",
            "SOL": "solana", "SOLANA": "solana",
            "BNB": "binancecoin",
            "XRP": "ripple",
            "DOGE": "dogecoin",
            "ADA": "cardano",
        }

        # Check for crypto
        for symbol, coin_id in crypto_map.items():
            if symbol in q:
                tasks.append({"type": "crypto", "params": {"coin_id": coin_id}})
                tasks.append({"type": "news", "params": {"query": coin_id, "limit": 5}})
                return tasks

        # Extract stock ticker — look for 1-5 uppercase letters
        # Also check for known company names
        company_map = {
            "NVIDIA": "NVDA", "APPLE": "AAPL", "MICROSOFT": "MSFT",
            "GOOGLE": "GOOGL", "ALPHABET": "GOOGL", "AMAZON": "AMZN",
            "TESLA": "TSLA", "META": "META", "NETFLIX": "NFLX",
            "AMD": "AMD", "INTEL": "INTC", "SAMSUNG": "005930.KS"
        }

        ticker = None
        for name, sym in company_map.items():
            if name in q:
                ticker = sym
                break

        if not ticker:
            # Try to extract ticker pattern from query
            tokens = re.findall(r'\b[A-Z]{1,5}\b', q)
            skip = {"A", "I", "IS", "THE", "AND", "OR", "FOR", "IN", "OF", "TO", "WHAT", "HOW", "SHOULD", "BUY", "SELL", "ME", "MY", "IT"}
            candidates = [t for t in tokens if t not in skip]
            if candidates:
                ticker = candidates[0]

        if ticker:
            tasks.append({"type": "stock", "params": {"ticker": ticker}})
            tasks.append({"type": "news", "params": {"query": ticker, "limit": 5}})
        else:
            # General market query — just fetch news
            tasks.append({"type": "news", "params": {"query": query, "limit": 5}})

        return tasks

research_workflow = ResearchWorkflow()
