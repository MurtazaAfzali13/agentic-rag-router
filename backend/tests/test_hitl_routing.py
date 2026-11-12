"""Unit tests for HITL routing edges and fallback copy."""
from app.agent.edges import route_after_analyzer, route_after_retriever, route_after_web_approval
from app.agent.nodes.fallback_not_found import NOT_FOUND_MESSAGE, fallback_not_found_node


def test_analyzer_web_goes_to_approval_not_search():
    assert route_after_analyzer({"route": "web"}) == "web_approval"


def test_retriever_miss_goes_to_approval():
    assert route_after_retriever({"documents": []}) == "web_approval"
    assert route_after_retriever({"documents": [{"text": "x"}]}) == "generator"


def test_approval_routes_yes_and_no():
    assert route_after_web_approval({"web_search_approved": True}) == "web_search"
    assert route_after_web_approval({"web_search_approved": False}) == "fallback_not_found"


def test_fallback_returns_fixed_message():
    result = fallback_not_found_node({})
    assert result["answer"] == NOT_FOUND_MESSAGE
    assert result["used_citations"] == []
