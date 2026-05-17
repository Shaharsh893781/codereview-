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
    gmail_user = os.getenv("GMAIL_USER", "")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    report_dir = Path("reports/generated")
    rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "80"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
