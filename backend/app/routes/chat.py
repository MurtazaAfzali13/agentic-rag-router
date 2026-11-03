"""POST /api/chat - runs the LangGraph agent and streams progress as Server-Sent Events.

Events:  route | step | sources | token | done | error
"""
import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agent.graph import rag_graph
from app.agent.utils import text_of
from app.core.config import get_settings
from app.schemas.chat import ChatRequest

log = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _run_agent(question: str, history: list[dict]) -> AsyncIterator[str]:
    initial = {"question": question, "history": history, "sources": []}
    try:
        async for mode, payload in rag_graph.astream(initial, stream_mode=["updates", "messages"]):
            if mode == "messages":
                chunk, meta = payload
                if meta.get("langgraph_node") == "generator":
                    text = text_of(chunk.content)
                    if text:
                        yield _sse("token", {"text": text})
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
                    if update.get("sources"):
                        yield _sse("sources", {"sources": update["sources"]})
                elif node == "web_search":
                    found = len(update.get("web_results", []))
                    yield _sse(
                        "step",
                        {"node": node, "label": f"Read {found} web result{'s' if found != 1 else ''} from Tavily"},
                    )
                    if update.get("sources"):
                        yield _sse("sources", {"sources": update["sources"]})
        yield _sse("done", {})
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
