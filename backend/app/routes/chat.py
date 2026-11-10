"""POST /api/chat - runs the LangGraph agent and streams progress as Server-Sent Events.

Events:  route | step | sources | token | done | error
Optional fields may be added; existing field names stay backward compatible.
"""
from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agent.citation_filter import StreamingCitationFilter
from app.agent.graph import rag_graph
from app.agent.utils import text_of
from app.core.config import get_settings
from app.schemas.chat import ChatRequest

log = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


def _sse(event: str, data: dict) -> str:
    payload = {**data, "t": int(time.time() * 1000)}
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _run_agent(question: str, history: list[dict]) -> AsyncIterator[str]:
    initial = {"question": question, "history": history, "sources": []}
    collected_sources: list[dict] = []
    citation_filter: StreamingCitationFilter | None = None
    used_citations: list[int] = []
    citations_valid = True

    try:
        async for mode, payload in rag_graph.astream(initial, stream_mode=["updates", "messages"]):
            if mode == "messages":
                chunk, meta = payload
                if meta.get("langgraph_node") == "generator":
                    text = text_of(chunk.content)
                    if text:
                        if citation_filter is None:
                            valid = {
                                int(s["n"])
                                for s in collected_sources
                                if isinstance(s.get("n"), int)
                            }
                            citation_filter = StreamingCitationFilter(valid)
                        safe = citation_filter.push(text)
                        if safe:
                            yield _sse("token", {"text": safe})
                continue

            for node, update in payload.items():
                update = update or {}
                if node == "analyzer":
                    yield _sse(
                        "route",
                        {
                            "route": update["route"],
                            "reason": update["route_reason"],
                            "search_query": update["search_query"],
                        },
                    )
                elif node == "retriever":
                    found = len(update.get("documents", []))
                    label = (
                        f"Found {found} relevant passage{'s' if found != 1 else ''} in your documents"
                        if found
                        else "Nothing relevant in your documents, falling back to web search"
                    )
                    yield _sse("step", {"node": node, "label": label})
                    sources = update.get("sources") or []
                    if sources:
                        collected_sources.extend(sources)
                        yield _sse("sources", {"sources": sources})
                elif node == "web_search":
                    found = len(update.get("web_results", []))
                    yield _sse(
                        "step",
                        {"node": node, "label": f"Read {found} web result{'s' if found != 1 else ''} from Tavily"},
                    )
                    sources = update.get("sources") or []
                    if sources:
                        collected_sources.extend(sources)
                        yield _sse("sources", {"sources": sources})
                elif node == "generator":
                    if citation_filter is not None:
                        trailing = citation_filter.flush()
                        if trailing:
                            yield _sse("token", {"text": trailing})
                    used_citations = list(update.get("used_citations") or [])
                    # If the model invented markers, the streaming filter dropped them;
                    # used_citations reflects the sanitized final answer.
                    valid = {
                        int(s["n"])
                        for s in collected_sources
                        if isinstance(s.get("n"), int)
                    }
                    citations_valid = all(n in valid for n in used_citations)

        yield _sse(
            "done",
            {
                "used_citations": used_citations,
                "citations_valid": citations_valid,
            },
        )
    except Exception as exc:
        log.exception("Agent run failed")
        yield _sse("error", {"message": f"The agent failed: {exc}"})


@router.post("/chat")
async def chat(request: ChatRequest):
    messages = request.messages
    if messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="The last message must come from the user.")

    settings = get_settings()
    history = [m.model_dump() for m in messages[:-1]][-settings.max_history_messages :]

    return StreamingResponse(
        _run_agent(messages[-1].content, history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )
