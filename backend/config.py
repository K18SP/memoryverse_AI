"""
Centralised settings loaded from .env
All modules import from here — never read os.environ directly.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Anthropic
    anthropic_api_key: str = "placeholder"

    # OpenAI
    openai_api_key: str = "placeholder"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "memoryverse"

    # Ollama local LLM
    ollama_url: str = "http://localhost:11434"

    # Supabase
    supabase_url: str = "placeholder"
    supabase_key: str = "placeholder"
    supabase_bucket: str = "memoryverse-files"

    # App
    app_env: str = "development"
    max_upload_size_mb: int = 20
    chunk_size: int = 512
    chunk_overlap: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()          # instantiated once, reused across the app
def get_settings() -> Settings:
    return Settings()
