"""
RESEARCH WORKFLOW
Active agents: FINIX + ROME + KOVA
Flow: FINIX → ROME (fetch) → KOVA (analyze via broker) → FINIX (synthesize)
Rome and Kova may communicate directly within this workflow scope.
"""
from agents.rome import rome
from agents.kova import kova
from services.gemini_service import gemini_service
from schemas.workflow_state import WorkflowState
from processors.market_processor import market_processor
from processors.ranking_processor import ranking_processor
from processors.risk_processor import risk_processor
from utils.logger import get_logger

logger = get_logger("workflow.research")

class ResearchWorkflow:
    def run(self, state: WorkflowState) -> WorkflowState:
        state.active_agents = ["finix", "rome", "kova"]
        query = state.original_query
        logger.info(f"Research workflow started | id: {state.workflow_id}")

        # STEP 1: Rome interprets query
        tasks = rome.interpret_query(query, state.context)
        if not tasks:
            logger.warning("Rome returned no tasks — falling back to news")
            tasks = [{"type": "news", "params": {"query": query, "limit": 5}}]

        logger.info(f"Rome tasks: {[t['type'] for t in tasks]}")
        state.results["fetch_tasks"] = [t["type"] for t in tasks]

        # STEP 2: Rome fetches all data
        raw_data = rome.fetch_all(tasks)
        state.results["raw_data_keys"] = list(raw_data.keys())

        # STEP 3: Python processors compute metrics
        processed = self._process_raw_data(raw_data)
        state.results["processed"] = processed

        # STEP 4: Broker call — Kova + FINIX in one Groq call
        kova_prompt = kova.build_analysis_prompt(processed, query)

        finix_prompt = f"""You are FINIX, a financial intelligence system.
Respond like an institutional analytics terminal. Not a chatbot. Not an educator.

Tone: concise, professional, evidence-driven, confidence-aware.
Do NOT use: "you should", "it's important to", "investing can be tricky", "let's take a look", "do your own research".
DO use: direct statements, quantitative evidence, structured observations.

User query: "{query}"

Format your response as:
ASSESSMENT: [1-2 sentence direct verdict]
KEY METRICS: [the most important numbers]
SIGNALS: [what the data indicates]
RISK FLAGS: [any concerns]
DISCLAIMER: Informational output only. Not financial advice."""

        broker_results = gemini_service.broker_call({
            "kova": kova_prompt,
            "finix": finix_prompt
        })

        kova_result = kova.parse_response(broker_results.get("kova", ""))
        finix_synthesis = broker_results.get("finix", "")

        if not finix_synthesis or len(finix_synthesis) < 80:
            finix_synthesis = gemini_service.call(
                prompt=f"""You are FINIX financial intelligence system.
Query: "{query}"
KOVA analysis: {kova_result['intelligence_brief']}
Processed data: {str(processed)[:1000]}
Respond in institutional terminal style. Concise, quantitative, direct.
Format: ASSESSMENT / KEY METRICS / SIGNALS / RISK FLAGS / DISCLAIMER"""
            )

        state.results["kova"] = kova_result
        state.results["finix_synthesis"] = finix_synthesis
        state.final_response = self._build_response(finix_synthesis, kova_result, processed, raw_data)
        logger.info(f"Research workflow completed | id: {state.workflow_id}")
        return state

    def _process_raw_data(self, raw_data: dict) -> dict:
        processed = {}
        for key, data in raw_data.items():
            if not isinstance(data, dict):
                processed[key] = data
                continue
            if data.get("error"):
                processed[key] = {"error": data["error"]}
                continue

            if key.startswith("stock") and "history" not in key and "results" not in str(data.keys()):
                processed[key] = market_processor.process_stock(data)

            elif key.startswith("stock_history"):
                history = data.get("history", [])
                processed[key] = market_processor.process_historical(history)

            elif key.startswith("bulk_stock") or key.startswith("nifty500"):
                results = data.get("results", {})
                if results:
                    processed_stocks = []
                    for ticker, ticker_data in results.items():
                        history = ticker_data.get("history", [])
                        if len(history) >= 2:
                            hist_result = market_processor.process_historical(history)
                            hist_result["ticker"] = ticker
                            processed_stocks.append(hist_result)
                    if processed_stocks:
                        ranked = ranking_processor.rank_by_return(
                            processed_stocks, key="period_return_pct", top_n=20
                        )
                        summary = ranking_processor.summarize_rankings(ranked, metric="period_return_pct")
                        processed[key] = {"type": "ranked_stocks", "rankings": summary}

            elif key.startswith("mutual_funds"):
                results = data.get("results", {})
                if results:
                    mf_processed = []
                    for code, fund_data in results.items():
                        start_nav = fund_data.get("start_nav", 0)
                        end_nav = fund_data.get("end_nav", 0)
                        period_return = round(
                            ((end_nav - start_nav) / start_nav * 100) if start_nav else 0, 2
                        )
                        mf_processed.append({
                            "scheme_code": code,
                            "scheme_name": fund_data.get("scheme_name", ""),
                            "fund_house": fund_data.get("fund_house", ""),
                            "category": fund_data.get("category", ""),
                            "start_nav": start_nav,
                            "end_nav": end_nav,
                            "metrics": {"period_return_pct": period_return}
                        })
                    if mf_processed:
                        ranked_mf = ranking_processor.rank_by_return(
                            mf_processed, key="period_return_pct", top_n=20
                        )
                        summary_mf = ranking_processor.summarize_rankings(ranked_mf, metric="period_return_pct")
                        processed[key] = {"type": "ranked_mutual_funds", "rankings": summary_mf}

            elif key.startswith("crypto"):
                processed[key] = market_processor.process_crypto(data)

            elif key.startswith("index_history"):
                history = data.get("history", [])
                processed[key] = market_processor.process_historical(history)

            elif key.startswith("index"):
                processed[key] = market_processor.process_stock(data)

            elif key.startswith("web_search") or key.startswith("news"):
                processed[key] = data

            else:
                processed[key] = data

        return processed

    def _build_response(self, synthesis: str, kova_result: dict,
                        processed: dict, raw_data: dict) -> dict:
        quant_data = {}
        for key, data in processed.items():
            if isinstance(data, dict):
                if data.get("type") == "ranked_stocks":
                    quant_data["stock_rankings"] = data.get("rankings", {})
                elif data.get("type") == "ranked_mutual_funds":
                    quant_data["mf_rankings"] = data.get("rankings", {})
                elif data.get("metrics"):
                    quant_data[key] = data.get("metrics", {})
        return {
            "summary": synthesis,
            "intelligence_brief": kova_result.get("intelligence_brief", ""),
            "quantitative_data": quant_data,
            "data_sources_used": list(raw_data.keys()),
            "disclaimer": "Informational output only. Not financial advice."
        }

research_workflow = ResearchWorkflow()
