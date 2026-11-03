"""Central application settings, loaded from environment / .env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenRouter
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_chat_model: str = "openai/gpt-4o-mini"
    openrouter_router_model: str = ""
    openrouter_embedding_model: str = "openai/text-embedding-3-small"
    embedding_dimension: int = 1536

    # Pinecone
    pinecone_api_key: str
    pinecone_index_name: str = "rag-router-agent"
    pinecone_namespace: str = "default"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    # Tavily
    tavily_api_key: str
    tavily_max_results: int = 5

    # RAG tuning
    chunk_size: int = 1000
    chunk_overlap: int = 150
    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.30
    max_history_messages: int = 10
    max_upload_mb: int = 25

    # Server
    cors_origins: str = "http://localhost:3000"
    app_url: str = "http://localhost:3000"
    app_name: str = "RAG Router Agent"
    data_dir: str = "data"

    @property
    def router_model(self) -> str:
        return self.openrouter_router_model or self.openrouter_chat_model

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def data_path(self) -> Path:
        path = Path(self.data_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
