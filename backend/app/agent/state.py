"""Shared state flowing through the LangGraph StateGraph."""
import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict, total=False):
    # input
    question: str
    history: list[dict]  # [{"role": "user"|"assistant", "content": str}]

    # Node 1 output
    route: str  # "pinecone" | "web" | "direct"
    route_reason: str
    search_query: str

    # Node 2 / 3 output
    documents: list[dict]
    web_results: list[dict]
    used_fallback: bool
    sources: Annotated[list[dict], operator.add]

    # Node 4 output
    answer: str
    used_citations: list[int]
