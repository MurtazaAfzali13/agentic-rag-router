"""Factories for OpenRouter-backed chat and embedding models.

OpenRouter exposes an OpenAI-compatible API, so we use the langchain-openai
classes and only change `base_url` and the attribution headers.
"""
from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import get_settings


def _headers() -> dict[str, str]:
    s = get_settings()
    return {"HTTP-Referer": s.app_url, "X-Title": s.app_name}


def get_chat_llm(*, temperature: float = 0.2) -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        model=s.openrouter_chat_model,
        api_key=s.openrouter_api_key,
        base_url=s.openrouter_base_url,
        temperature=temperature,
        streaming=True,
        default_headers=_headers(),
    )


def get_router_llm() -> ChatOpenAI:
    """Small, deterministic model used by the analyzer node."""
    s = get_settings()
    return ChatOpenAI(
        model=s.router_model,
        api_key=s.openrouter_api_key,
        base_url=s.openrouter_base_url,
        temperature=0,
        max_tokens=300,
        streaming=False,
        default_headers=_headers(),
    )


@lru_cache
def get_embeddings() -> OpenAIEmbeddings:
    s = get_settings()
    return OpenAIEmbeddings(
        model=s.openrouter_embedding_model,
        api_key=s.openrouter_api_key,
        base_url=s.openrouter_base_url,
        default_headers=_headers(),
        # OpenRouter expects raw strings, not pre-tokenised arrays.
        check_embedding_ctx_length=False,
    )
