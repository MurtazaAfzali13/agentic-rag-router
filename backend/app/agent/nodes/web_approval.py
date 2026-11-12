"""HITL gate: pause before any web search until the user approves."""
from __future__ import annotations

from langgraph.types import interrupt

from app.agent.state import AgentState

APPROVAL_MESSAGE = (
    "The requested information is not available in your uploaded PDF. "
    "Would you like me to search the internet to find the answer?"
)


def web_approval_node(state: AgentState) -> dict:
    """Interrupt the graph and wait for a YES/NO resume value."""
    decision = interrupt(
        {
            "type": "web_search_approval",
            "message": APPROVAL_MESSAGE,
            "search_query": state.get("search_query") or state.get("question", ""),
            "reason": state.get("route_reason", ""),
            "route": state.get("route", "web"),
        }
    )
    approved = str(decision).strip().upper() in {"YES", "Y", "TRUE", "1", "APPROVE"}
    return {"web_search_approved": approved}
