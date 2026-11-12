
from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agent.edges import route_after_analyzer, route_after_retriever, route_after_web_approval
from app.agent.nodes.analyzer import analyzer_node
from app.agent.nodes.fallback_not_found import fallback_not_found_node
from app.agent.nodes.generator import generator_node
from app.agent.nodes.retriever import retriever_node
from app.agent.nodes.web_approval import web_approval_node
from app.agent.nodes.web_search import web_search_node
from app.agent.state import AgentState

_rag_graph: Any | None = None


def build_graph(*, checkpointer=None):
    graph = StateGraph(AgentState)

    graph.add_node("analyzer", analyzer_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("web_approval", web_approval_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("fallback_not_found", fallback_not_found_node)
    graph.add_node("generator", generator_node)

    graph.add_edge(START, "analyzer")
    graph.add_conditional_edges(
        "analyzer",
        route_after_analyzer,
        {"retriever": "retriever", "web_approval": "web_approval", "generator": "generator"},
    )
    graph.add_conditional_edges(
        "retriever",
        route_after_retriever,
        {"generator": "generator", "web_approval": "web_approval"},
    )
    graph.add_conditional_edges(
        "web_approval",
        route_after_web_approval,
        {"web_search": "web_search", "fallback_not_found": "fallback_not_found"},
    )
    graph.add_edge("web_search", "generator")
    graph.add_edge("generator", END)
    graph.add_edge("fallback_not_found", END)

    return graph.compile(checkpointer=checkpointer)


def init_rag_graph(*, checkpointer) -> Any:
    """Compile the production graph with the given async checkpointer."""
    global _rag_graph
    _rag_graph = build_graph(checkpointer=checkpointer)
    return _rag_graph


def reset_rag_graph() -> None:
    """Clear the compiled graph (called on app shutdown)."""
    global _rag_graph
    _rag_graph = None


def get_rag_graph():
    """Return the lifespan-initialized graph (AsyncSqliteSaver-backed)."""
    if _rag_graph is None:
        raise RuntimeError(
            "RAG graph is not initialized. Ensure the FastAPI lifespan opened AsyncSqliteSaver."
        )
    return _rag_graph


# Back-compat alias used by older imports.
def __getattr__(name: str):
    if name == "rag_graph":
        return get_rag_graph()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
