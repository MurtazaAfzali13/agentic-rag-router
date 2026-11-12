"""POST /api/chat and /api/chat/resume — LangGraph agent over SSE with HITL pause.

Events:  route | step | sources | token | interrupt | done | error
Optional fields may be added; existing field names stay backward compatible.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langgraph.types import Command

from app.agent.citation_filter import StreamingCitationFilter
from app.agent.graph import get_rag_graph
from app.agent.utils import text_of
from app.core.config import get_settings
from app.schemas.chat import ChatRequest, ChatResumeRequest

log = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


def _sse(event: str, data: dict) -> str:
    payload = {**data, "t": int(time.time() * 1000)}
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def _interrupt_payload(snapshot: Any) -> dict | None:
    """Extract the first pending interrupt value from a state snapshot."""
    interrupts = getattr(snapshot, "interrupts", None) or ()
    if not interrupts:
        # Older/alternate shape: tasks[].interrupts
        for task in getattr(snapshot, "tasks", ()) or ():
            task_interrupts = getattr(task, "interrupts", None) or ()
            if task_interrupts:
                interrupts = task_interrupts
                break
    if not interrupts:
        return None
    value = getattr(interrupts[0], "value", interrupts[0])
    return value if isinstance(value, dict) else {"message": str(value)}


async def _stream_graph(
    *,
    input_payload: Any,
    thread_id: str,
    collected_sources: list[dict] | None = None,
) -> AsyncIterator[str]:
    """Run/resume the graph via astream and yield SSE frames until done or interrupt."""
    graph = get_rag_graph()  # AsyncSqliteSaver-backed; opened in FastAPI lifespan
    config = _config(thread_id)
    collected_sources = collected_sources if collected_sources is not None else []
    citation_filter: StreamingCitationFilter | None = None
    used_citations: list[int] = []
    citations_valid = True

    try:
        async for mode, payload in graph.astream(
            input_payload,
            config=config,
            stream_mode=["updates", "messages"],
        ):
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
                            "thread_id": thread_id,
                        },
                    )
                elif node == "retriever":
                    found = len(update.get("documents", []))
                    label = (
                        f"Found {found} relevant passage{'s' if found != 1 else ''} in your documents"
                        if found
                        else "Nothing relevant in your documents — waiting for web-search approval"
                    )
                    yield _sse("step", {"node": node, "label": label})
                    sources = update.get("sources") or []
                    if sources:
                        collected_sources.extend(sources)
                        yield _sse("sources", {"sources": sources})
                elif node == "web_approval":
                    # Node only returns after resume; emit a quiet step for the timeline.
                    approved = bool(update.get("web_search_approved"))
                    yield _sse(
                        "step",
                        {
                            "node": node,
                            "label": "Web search approved" if approved else "Web search declined",
                        },
                    )
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
                elif node == "fallback_not_found":
                    answer = update.get("answer") or ""
                    if answer:
                        yield _sse("token", {"text": answer})
                    yield _sse(
                        "step",
                        {"node": node, "label": "Stopped without searching the web"},
                    )
                    used_citations = list(update.get("used_citations") or [])
                elif node == "generator":
                    if citation_filter is not None:
                        trailing = citation_filter.flush()
                        if trailing:
                            yield _sse("token", {"text": trailing})
                    used_citations = list(update.get("used_citations") or [])
                    valid = {
                        int(s["n"])
                        for s in collected_sources
                        if isinstance(s.get("n"), int)
                    }
                    citations_valid = all(n in valid for n in used_citations)

        snapshot = await graph.aget_state(config)
        pending = _interrupt_payload(snapshot)
        if pending is not None:
            yield _sse(
                "interrupt",
                {
                    "thread_id": thread_id,
                    "type": pending.get("type", "web_search_approval"),
                    "message": pending.get(
                        "message",
                        "Would you like me to search the internet to find the answer?",
                    ),
                    "search_query": pending.get("search_query", ""),
                    "reason": pending.get("reason", ""),
                    "route": pending.get("route", "web"),
                },
            )
            return

        yield _sse(
            "done",
            {
                "thread_id": thread_id,
                "used_citations": used_citations,
                "citations_valid": citations_valid,
            },
        )
    except Exception as exc:
        log.exception("Agent run failed")
        yield _sse("error", {"message": f"The agent failed: {exc}", "thread_id": thread_id})


async def _run_agent(question: str, history: list[dict], thread_id: str) -> AsyncIterator[str]:
    initial = {"question": question, "history": history, "sources": []}
    async for frame in _stream_graph(input_payload=initial, thread_id=thread_id):
        yield frame


async def _resume_agent(thread_id: str, decision: str) -> AsyncIterator[str]:
    async for frame in _stream_graph(input_payload=Command(resume=decision), thread_id=thread_id):
        yield frame


@router.post("/chat")
async def chat(request: ChatRequest):
    messages = request.messages
    if messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="The last message must come from the user.")

    settings = get_settings()
    history = [m.model_dump() for m in messages[:-1]][-settings.max_history_messages :]
    thread_id = (request.thread_id or "").strip() or uuid.uuid4().hex

    return StreamingResponse(
        _run_agent(messages[-1].content, history, thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Thread-Id": thread_id,
        },
    )


@router.post("/chat/resume")
async def chat_resume(request: ChatResumeRequest):
    graph = get_rag_graph()
    config = _config(request.thread_id)
    snapshot = await graph.aget_state(config)
    if snapshot.values is None and not snapshot.next:
        raise HTTPException(status_code=404, detail="Unknown or expired thread_id.")
    if _interrupt_payload(snapshot) is None and not snapshot.next:
        raise HTTPException(status_code=409, detail="This thread is not waiting for approval.")

    return StreamingResponse(
        _resume_agent(request.thread_id, request.decision),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Thread-Id": request.thread_id,
        },
    )
