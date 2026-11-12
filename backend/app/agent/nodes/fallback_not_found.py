"""Deterministic refusal when the user declines a web search after a PDF miss."""
from __future__ import annotations

from app.agent.state import AgentState

NOT_FOUND_MESSAGE = "I could not find this information in your provided PDF documents."


def fallback_not_found_node(_state: AgentState) -> dict:
    """Return a fixed answer — never call an LLM or invent facts."""
    return {
        "answer": NOT_FOUND_MESSAGE,
        "used_citations": [],
        "web_results": [],
    }
