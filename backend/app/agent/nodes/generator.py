"""Node 4 - Answer generator. Tokens are streamed by LangGraph (stream_mode='messages')."""
from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agent.citation_filter import sanitize_citations
from app.agent.state import AgentState
from app.agent.utils import text_of
from app.llm.client import get_chat_llm
from app.prompts.generator_prompt import build_system_prompt


def _build_context(documents: list[dict], web_results: list[dict]) -> str:
    blocks: list[str] = []
    n = 1
    for d in documents:
        label = d.get("n", n)
        blocks.append(f"[{label}] PDF '{d['filename']}', page {d['page']}\n{d['text']}")
        n = int(label) + 1
    for w in web_results:
        label = w.get("n", n)
        blocks.append(f"[{label}] Web: {w['title']} ({w['url']})\n{w['content']}")
        n = int(label) + 1
    return "\n\n".join(blocks)


def _valid_citation_numbers(documents: list[dict], web_results: list[dict]) -> set[int]:
    nums: set[int] = set()
    n = 1
    for d in documents:
        nums.add(int(d.get("n", n)))
        n = int(d.get("n", n)) + 1
    for w in web_results:
        nums.add(int(w.get("n", n)))
        n = int(w.get("n", n)) + 1
    return nums


def _history_messages(history: list[dict]) -> list[BaseMessage]:
    return [
        HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
        for m in history
    ]


async def generator_node(state: AgentState, config: RunnableConfig) -> dict:
    documents = state.get("documents") or []
    web_results = state.get("web_results") or []
    valid = _valid_citation_numbers(documents, web_results)

    system_prompt = build_system_prompt(
        has_pdf_context=bool(documents),
        has_web_context=bool(web_results),
        retrieval_attempted=state.get("route") in ("pinecone", "web"),
        used_fallback=bool(state.get("used_fallback")),
        context_block=_build_context(documents, web_results),
    )

    messages: list[BaseMessage] = [
        SystemMessage(content=system_prompt),
        *_history_messages(state.get("history", [])),
        HumanMessage(content=state["question"]),
    ]
    response = await get_chat_llm().ainvoke(messages, config)
    raw = text_of(response.content)
    answer, used_citations = sanitize_citations(raw, valid)
    return {"answer": answer, "used_citations": used_citations}
