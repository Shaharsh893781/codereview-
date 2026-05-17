from functools import lru_cache
from pathlib import Path
import os


class Settings:
    app_name = "CodeReviewAI"
    database_url = os.getenv("DATABASE_URL", "sqlite:///./codereviewai.db")
    secret_key = os.getenv("SECRET_KEY", "development-secret-key")
    algorithm = "HS256"
    access_token_expire_minutes = 60 * 8
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    report_dir = Path("reports/generated")
    rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "80"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
