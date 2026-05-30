import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AI
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # APIs
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # Auth
    ADMIN_KEY: str = os.getenv("ADMIN_KEY", "")

    # App
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Source quality framework
    PREFERRED_SOURCES: list = [
        "reuters.com", "ft.com", "wsj.com", "bloomberg.com",
        "cnbc.com", "marketwatch.com", "economictimes.indiatimes.com",
        "moneycontrol.com", "livemint.com", "businessstandard.com",
        "federalreserve.gov", "rbi.org.in", "sebi.gov.in",
        "imf.org", "worldbank.org", "ecb.europa.eu"
    ]

    EXCLUDED_SOURCES: list = [
        "aljazeera.com",
        "aljazeera.net",
    ]

    @classmethod
    def validate(cls):
        missing = []
        if not cls.GROQ_API_KEY:
            missing.append("GROQ_API_KEY")
        if not cls.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not cls.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if missing:
            raise EnvironmentError(f"Missing: {', '.join(missing)}")

config = Config()
