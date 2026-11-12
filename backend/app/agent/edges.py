"""Conditional routing functions for the graph."""
from typing import Literal

from app.agent.state import AgentState


def route_after_analyzer(state: AgentState) -> Literal["retriever", "web_approval", "generator"]:
    route = state.get("route", "direct")
    if route == "pinecone":
        return "retriever"
    if route == "web":
        return "web_approval"
    return "generator"


def route_after_retriever(state: AgentState) -> Literal["generator", "web_approval"]:
    """If the PDFs contain nothing relevant, pause for web-search approval."""
    return "generator" if state.get("documents") else "web_approval"


def route_after_web_approval(state: AgentState) -> Literal["web_search", "fallback_not_found"]:
    """Resume path: YES continues to Tavily; NO returns a fixed not-found answer."""
    return "web_search" if state.get("web_search_approved") else "fallback_not_found"
