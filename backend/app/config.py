from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "GAME NEXUS API"
    environment: str = "development"
    frontend_origin: str = "http://127.0.0.1:8000"
    database_url: str
    jwt_secret_key: str
    jwt_expire_minutes: int = 60
    cookie_secure: bool = False
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://127.0.0.1:8000/api/auth/google/callback"
    email_host: str = "smtp.gmail.com"
    email_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_from: str = ""
    session_secret: str = "change-this-session-secret"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    razorpay_monthly_plan_id: str = ""
    razorpay_yearly_plan_id: str = ""
    model_config = SettingsConfigDict(
    env_file=Path(__file__).resolve().parents[1] / ".env",
    extra="ignore"
)

settings = Settings()
