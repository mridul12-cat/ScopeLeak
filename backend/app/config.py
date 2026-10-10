import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

class Settings:
    @property
    def HOST(self) -> str:
        return os.getenv("HOST", "0.0.0.0")

    @property
    def PORT(self) -> int:
        return int(os.getenv("PORT", "8000"))

    @property
    def ENVIRONMENT(self) -> str:
        return os.getenv("ENVIRONMENT", "development")

    @property
    def DATABASE_URL(self) -> str:
        return os.getenv("DATABASE_URL", "sqlite:///./scopeleak.db")

    @property
    def GEMINI_API_KEY(self) -> str:
        return os.getenv("GEMINI_API_KEY", "").strip()

    @property
    def GEMINI_MODEL(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

    @property
    def GEMINI_THINKING_LEVEL(self) -> str:
        level = os.getenv("GEMINI_THINKING_LEVEL", "low").strip().lower()
        if level in ("low", "medium", "high"):
            return level
        return "low"

    @property
    def GEMINI_TIMEOUT_SECONDS(self) -> float:
        try:
            return float(os.getenv("GEMINI_TIMEOUT_SECONDS", "35.0"))
        except ValueError:
            return 35.0

    @property
    def UPLOAD_DIR(self) -> str:
        return os.getenv("UPLOAD_DIR", "./uploads")

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return 15 * 1024 * 1024  # 15 MB

settings = Settings()
