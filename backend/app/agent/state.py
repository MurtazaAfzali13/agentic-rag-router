"""Shared state flowing through the LangGraph StateGraph."""
import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict, total=False):
    question: str
    history: list[dict]  

    route: str 
    route_reason: str
    search_query: str

    documents: list[dict]
    web_results: list[dict]
    used_fallback: bool
    sources: Annotated[list[dict], operator.add]

    web_search_approved: bool

    answer: str
    used_citations: list[int]
