"""Tavily live web search."""
from functools import lru_cache

from tavily import AsyncTavilyClient

from app.core.config import get_settings


@lru_cache
def _client() -> AsyncTavilyClient:
    return AsyncTavilyClient(api_key=get_settings().tavily_api_key)


async def web_search(query: str) -> list[dict]:
    s = get_settings()
    response = await _client().search(
        query=query,
        max_results=s.tavily_max_results,
        search_depth="advanced",
        include_answer=False,
    )
    return [
        {
            "title": r.get("title") or r.get("url", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": float(r.get("score") or 0),
        }
        for r in response.get("results", [])
    ]
