"""Node 1 - Request analyzer: decides pinecone / web / direct."""
import asyncio
import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.state import AgentState
from app.agent.utils import text_of
from app.llm.client import get_router_llm
from app.prompts.router_prompt import (
    ROUTER_SYSTEM_PROMPT,
    ROUTER_USER_TEMPLATE,
    format_documents,
    format_history,
)
from app.services import document_registry

log = logging.getLogger(__name__)
_VALID_ROUTES = {"pinecone", "web", "direct"}


def _parse_json(raw: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    return json.loads(match.group(0) if match else cleaned)


async def analyzer_node(state: AgentState) -> dict:
    question = state["question"]
    docs = await asyncio.to_thread(document_registry.list_documents)
    has_docs = bool(docs)

    route = "pinecone" if has_docs else "web"
    reason = "Default routing (router model unavailable)."
    search_query = question

    try:
        prompt = ROUTER_USER_TEMPLATE.format(
            documents=format_documents([d["filename"] for d in docs]),
            history=format_history(state.get("history", [])),
            question=question,
        )
        result = await get_router_llm().ainvoke(
            [SystemMessage(content=ROUTER_SYSTEM_PROMPT), HumanMessage(content=prompt)]
        )
        data = _parse_json(text_of(result.content))
        if data.get("route") in _VALID_ROUTES:
            route = data["route"]
        reason = str(data.get("reason") or reason)[:240]
        search_query = str(data.get("search_query") or question).strip() or question
    except Exception as exc:  # never let routing break the chat
        log.warning("Router failed, using default route '%s': %s", route, exc)

    if route == "pinecone" and not has_docs:
        route, reason = "web", "No documents uploaded, searching the web instead."

    return {"route": route, "route_reason": reason, "search_query": search_query}
