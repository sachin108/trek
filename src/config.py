from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=Path(__file__).parent / ".env", extra="ignore")
    # Pydantic automatically looks for DATABASE_URL and SECRET_KEY in the system
    # environment and falls back to the .env file

@lru_cache
def get_settings() -> Settings:
    return Settings()
    # Wrapping the settings instantiation in lru_cache ensures FastAPI only
    # reads the .env file once on startup rather than reloading it on every request.

settings = get_settings()