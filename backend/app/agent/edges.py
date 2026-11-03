"""Conditional routing functions for the graph."""
from typing import Literal

from app.agent.state import AgentState


def route_after_analyzer(state: AgentState) -> Literal["retriever", "web_search", "generator"]:
    route = state.get("route", "direct")
    if route == "pinecone":
        return "retriever"
    if route == "web":
        return "web_search"
    return "generator"


def route_after_retriever(state: AgentState) -> Literal["generator", "web_search"]:
    """If the PDFs contain nothing relevant, fall back to live web search."""
    return "generator" if state.get("documents") else "web_search"
