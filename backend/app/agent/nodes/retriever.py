"""Node 2 - Retrieval from Pinecone."""
import asyncio
import logging

from app.agent.state import AgentState
from app.core.config import get_settings
from app.services.vectorstore import get_vectorstore

log = logging.getLogger(__name__)


async def retriever_node(state: AgentState) -> dict:
    s = get_settings()
    query = state.get("search_query") or state["question"]

    try:
        matches = await asyncio.to_thread(get_vectorstore().query, query, s.retrieval_top_k)
    except Exception as exc:
        log.error("Pinecone retrieval failed: %s", exc)
        matches = []

    relevant = [m for m in matches if m["score"] >= s.retrieval_min_score and m["text"].strip()]
    sources = [
        {
            "type": "pdf",
            "title": m["filename"],
            "page": m["page"],
            "score": round(m["score"], 3),
            "snippet": m["text"][:280],
        }
        for m in relevant
    ]
    return {"documents": relevant, "sources": sources}
