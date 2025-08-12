from typing import Optional, Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENAI_API_KEY: Optional[str] = None
    MODEL_PLANNER: str = "gpt-4o-mini"
    MODEL_ANSWERER: str = "gpt-4o-mini"

    # Timeouts (seconds)
    GLOBAL_TIMEOUT: int = 170
    TOOL_TIMEOUT: int = 40

    # Limits
    MAX_UPLOAD_BYTES: int = 25 * 1024 * 1024  # 25 MB per file
    MAX_PLOT_BYTES: int = 100_000

    # Security / allowlists (e.g., ("en.wikipedia.org",))
    HTTP_ALLOWLIST: Tuple[str, ...] = tuple()

    # pydantic v2 settings config
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
