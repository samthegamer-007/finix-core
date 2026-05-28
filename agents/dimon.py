"""
DIMON — Financial Reasoning & Decision Agent
NOT built in Phase 1. Stub only.
Will handle: investment reasoning, risk evaluation, trade justification.
Named after Jamie Dimon — the senior analyst who makes the call.
"""
from utils.logger import get_logger

logger = get_logger("dimon")

class Dimon:
    def __init__(self):
        logger.info("Dimon initialized (stub — active from Phase decision workflow)")

    def reason(self, insights: dict) -> dict:
        """Placeholder. Will use Gemini broker call in Phase decision workflow."""
        raise NotImplementedError("Dimon is not active yet. Build decision workflow first.")

dimon = Dimon()
