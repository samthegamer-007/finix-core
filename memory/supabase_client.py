"""
Supabase client — wired in Phase 7.
Placeholder for now. Frank uses in-memory dict until this is connected.
"""
from utils.logger import get_logger

logger = get_logger("supabase_client")

class SupabaseClient:
    def __init__(self):
        logger.info("SupabaseClient stub initialized (Phase 7)")

    def connect(self):
        raise NotImplementedError("Supabase connection wired in Phase 7")

supabase_client = SupabaseClient()
