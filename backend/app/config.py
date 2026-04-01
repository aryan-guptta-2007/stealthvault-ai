"""
StealthVault AI - Configuration
Centralized settings for the entire system.
"""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional

# Load environment variables from .env file (Option 🎯 RESULT)
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "StealthVault AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False # 🛡️ Hardened default for production
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 🧱 Infrastructure Hardening (Elite Tier)
    MAX_PAYLOAD_BYTES: int = 1024 * 1024 # 1MB Limit
    ALERTS_RETENTION_DAYS: int = 30
    LOGS_RETENTION_DAYS: int = 7

    # Persistence & Messaging
    # Persistence & Messaging
    DATABASE_URL: str = os.getenv("SV_DATABASE_URL", "sqlite+aiosqlite:///./stealthvault.db")
    REDIS_URL: Optional[str] = None

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v

    # AI Engine
    ANOMALY_CONTAMINATION: float = 0.1  # Expected fraction of anomalies
    ANOMALY_THRESHOLD: float = 0.7
    CLASSIFIER_CONFIDENCE_THRESHOLD: float = 0.6
    RISK_CRITICAL_THRESHOLD: float = 0.85
    RISK_HIGH_THRESHOLD: float = 0.65
    RISK_MEDIUM_THRESHOLD: float = 0.4

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = ""
    MODELS_DIR: str = ""

    # Alert Storage
    MAX_ALERTS: int = 1000
    MAX_TRAFFIC_HISTORY: int = 5000

    # Redis Queue Control (Prevent OOM/Lag)
    MAX_QUEUE_SIZE: int = 50000
    CONGESTION_THRESHOLD: int = 10000
    CRITICAL_THRESHOLD: int = 30000

    # WebSocket
    WS_BROADCAST_INTERVAL: float = 1.0

    # 🔐 Security & Auth (Elite Tier)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET_KEY: Optional[str] = os.getenv("SV_JWT_SECRET_KEY")

    # 🔔 External Notifications (Option 3)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    SLACK_WEBHOOK_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        env_prefix = "SV_"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.DATA_DIR:
            self.DATA_DIR = os.path.join(self.BASE_DIR, "data")
        if not self.MODELS_DIR:
            self.MODELS_DIR = os.path.join(self.BASE_DIR, "data", "models")

        # Ensure directories exist
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.MODELS_DIR, exist_ok=True)
        os.makedirs(os.path.join(self.DATA_DIR, "datasets"), exist_ok=True)


settings = Settings()
