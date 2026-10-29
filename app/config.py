# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # required: app wont start without this
    gemini_api_key: str 
    gemini_models: list[str]

    # defaults
    allowed_origins: list[str] = ["http://localhost:3000"]
    max_message_chars: int = 500
    max_history_turns: int = 6
    rate_limit: str = "10/minute"

settings = Settings() # pyright: ignore[reportCallIssue]