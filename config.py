# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- existing ---
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200
    SMTP_EMAIL: str = ""
    SMTP_APP_PASSWORD: str = ""
    APP_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # --- NEW: AWS / S3 ---
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET: str
    S3_PUBLIC_BASE_URL: str  # e.g. https://theplanbeyond.s3.ap-south-1.amazonaws.com

    # pydantic v2 style config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",        # <-- prevents "Extra inputs are not permitted"
        case_sensitive=True,   # field names match your UPPERCASE env keys
    )

settings = Settings()
