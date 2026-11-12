"""Integration-style test: interrupt before web_search, then YES/NO resume (async)."""
from __future__ import annotations

import asyncio

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from app.agent.edges import route_after_web_approval
from app.agent.nodes.fallback_not_found import NOT_FOUND_MESSAGE, fallback_not_found_node
from app.agent.nodes.web_approval import APPROVAL_MESSAGE, web_approval_node
from app.agent.state import AgentState


def _approval_graph(checkpointer):
    graph = StateGraph(AgentState)
    graph.add_node("web_approval", web_approval_node)
    graph.add_node("fallback_not_found", fallback_not_found_node)
    graph.add_node("web_search", lambda _state: {"web_results": [{"title": "ok"}], "sources": []})
    graph.add_edge(START, "web_approval")
    graph.add_conditional_edges(
        "web_approval",
        route_after_web_approval,
        {"web_search": "web_search", "fallback_not_found": "fallback_not_found"},
    )
    graph.add_edge("web_search", END)
    graph.add_edge("fallback_not_found", END)
    return graph.compile(checkpointer=checkpointer)


async def _decline_flow() -> None:
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        await checkpointer.setup()
        graph = _approval_graph(checkpointer)
        config = {"configurable": {"thread_id": "t-decline"}}

        await graph.ainvoke(
            {
                "question": "What is the weather in Paris?",
                "history": [],
                "sources": [],
                "search_query": "weather Paris",
                "route": "web",
                "route_reason": "live data",
            },
            config=config,
        )

        snapshot = await graph.aget_state(config)
        assert snapshot.next
        assert snapshot.interrupts
        assert snapshot.interrupts[0].value["message"] == APPROVAL_MESSAGE

        final = await graph.ainvoke(Command(resume="NO"), config=config)
        assert final["answer"] == NOT_FOUND_MESSAGE
        assert final.get("web_search_approved") is False
        assert not final.get("web_results")


async def _approve_flow() -> None:
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        await checkpointer.setup()
        graph = _approval_graph(checkpointer)
        config = {"configurable": {"thread_id": "t-approve"}}

        await graph.ainvoke(
            {
                "question": "weather?",
                "history": [],
                "sources": [],
                "search_query": "weather",
                "route": "web",
                "route_reason": "live data",
            },
            config=config,
        )
        assert (await graph.aget_state(config)).interrupts

        final = await graph.ainvoke(Command(resume="YES"), config=config)
        assert final.get("web_search_approved") is True
        assert final.get("web_results") == [{"title": "ok"}]


def test_interrupt_then_decline_returns_fixed_message():
    asyncio.run(_decline_flow())


def test_interrupt_then_approve_runs_web_search():
    asyncio.run(_approve_flow())
