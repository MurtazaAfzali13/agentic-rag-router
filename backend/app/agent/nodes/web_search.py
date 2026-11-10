"""Node 3 - Live web search with Tavily."""
from __future__ import annotations

import logging

from app.agent.state import AgentState
from app.services.tavily_service import web_search

log = logging.getLogger(__name__)


async def web_search_node(state: AgentState) -> dict:
    query = state.get("search_query") or state["question"]
    # We reach this node from the retriever only when the PDFs had no answer.
    used_fallback = state.get("route") == "pinecone"

    try:
        results = await web_search(query)
    except Exception as exc:
        log.error("Tavily search failed: %s", exc)
        results = []

    # PDF sources are numbered first; continue from len(documents) + 1.
    start_n = len(state.get("documents") or []) + 1
    sources = []
    numbered_results = []
    for offset, result in enumerate(results):
        n = start_n + offset
        content = result.get("content", "") or ""
        sources.append(
            {
                "type": "web",
                "n": n,
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "score": round(float(result.get("score", 0)), 3),
                "snippet": content,  # full passage for reader pane
                "text": content,
            }
        )
        numbered_results.append({**result, "n": n})

    return {"web_results": numbered_results, "sources": sources, "used_fallback": used_fallback}
