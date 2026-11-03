"""Node 3 - Live web search with Tavily."""
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

    sources = [
        {
            "type": "web",
            "title": r["title"],
            "url": r["url"],
            "score": round(r["score"], 3),
            "snippet": r["content"][:280],
        }
        for r in results
    ]
    return {"web_results": results, "sources": sources, "used_fallback": used_fallback}
