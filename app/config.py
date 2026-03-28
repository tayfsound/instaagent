from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    INSTAGRAM_VERIFY_TOKEN: str = "benim-token-123"
    INSTAGRAM_ACCESS_TOKEN: str = "placeholder"
    INSTAGRAM_PAGE_ID: str = "placeholder"
    ANTHROPIC_API_KEY: str = "placeholder"
    DATABASE_URL: str = "postgresql://placeholder"
    DASHBOARD_USERNAME: str = "admin"
    DASHBOARD_PASSWORD: str = "Admin1234!"
    SECRET_KEY: str = "instaagent-super-secret-key-2024"
    AUTO_REPLY_CONFIDENCE_THRESHOLD: float = 0.90
    ENVIRONMENT: str = "production"

    class Config:
        env_file = ".env"

settings = Settings()
