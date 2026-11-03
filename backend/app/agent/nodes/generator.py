"""Node 4 - Answer generator. Tokens are streamed by LangGraph (stream_mode='messages')."""
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agent.state import AgentState
from app.agent.utils import text_of
from app.llm.client import get_chat_llm
from app.prompts.generator_prompt import build_system_prompt


def _build_context(documents: list[dict], web_results: list[dict]) -> str:
    blocks: list[str] = []
    n = 1
    for d in documents:
        blocks.append(f"[{n}] PDF '{d['filename']}', page {d['page']}\n{d['text']}")
        n += 1
    for w in web_results:
        blocks.append(f"[{n}] Web: {w['title']} ({w['url']})\n{w['content']}")
        n += 1
    return "\n\n".join(blocks)


def _history_messages(history: list[dict]) -> list[BaseMessage]:
    return [
        HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
        for m in history
    ]


async def generator_node(state: AgentState, config: RunnableConfig) -> dict:
    documents = state.get("documents") or []
    web_results = state.get("web_results") or []

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
    return {"answer": text_of(response.content)}
