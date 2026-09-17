import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
SESSIONS_DIR = STORAGE_DIR / "sessions"
TESTS_DIR = STORAGE_DIR / "generated-tests"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
TESTS_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI QA Agent"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"

    DATABASE_URL: str = f"sqlite+aiosqlite:///{STORAGE_DIR}/qa_agent.db"

    STORAGE_PATH: Path = STORAGE_DIR
    SESSIONS_PATH: Path = SESSIONS_DIR
    TESTS_PATH: Path = TESTS_DIR

    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "codex"  # codex, openai, gemini, anthropic
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-5.6-luna"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Browser settings
    DEFAULT_HEADLESS: bool = False
    BROWSER_VIEWPORT_WIDTH: int = 1280
    BROWSER_VIEWPORT_HEIGHT: int = 800
    ACTION_TIMEOUT_MS: int = 8000
    MAX_REPRODUCTION_ATTEMPTS: int = 2
    LOOP_REPEAT_THRESHOLD: int = 3

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
