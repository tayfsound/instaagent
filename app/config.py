"""
Uygulama konfigürasyonu — tüm env değişkenleri buradan okunur.
.env dosyasına veya Render dashboard'una eklenecek.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Instagram / Meta ---
    INSTAGRAM_VERIFY_TOKEN: str        # Webhook doğrulama token'ı (sen belirle)
    INSTAGRAM_ACCESS_TOKEN: str        # Meta Graph API access token
    INSTAGRAM_PAGE_ID: str             # Instagram Business Page ID

    # --- Anthropic (Claude) ---
    ANTHROPIC_API_KEY: str             # sk-ant-...

    # --- Supabase / PostgreSQL ---
    DATABASE_URL: str                  # postgresql://user:pass@host:5432/db

    # --- Auth (Dashboard girişi) ---
    DASHBOARD_USERNAME: str = "admin"
    DASHBOARD_PASSWORD: str = "changeme123"
    SECRET_KEY: str = "super-secret-jwt-key-change-this"

    # --- Genel ---
    AUTO_REPLY_CONFIDENCE_THRESHOLD: float = 0.90  # %90 üstü otomatik gönder
    ENVIRONMENT: str = "production"

    class Config:
        env_file = ".env"


settings = Settings()
