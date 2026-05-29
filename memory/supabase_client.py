from supabase import create_client, Client
from config import config
from utils.logger import get_logger

logger = get_logger("supabase_client")

class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_KEY
        )
        logger.info("Supabase client initialized")

    def get(self) -> Client:
        return self.client

supabase_client = SupabaseClient()
