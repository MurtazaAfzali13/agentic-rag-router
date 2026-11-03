"""LangGraph assembly.

            +-----------+
 START ---> | analyzer  |
            +-----+-----+
     pinecone |   | web       | direct
              v   v           |
       +-----------+  no docs |
       | retriever |--------+ |
       +-----+-----+        v |
         docs |        +------------+
              |        | web_search |
              |        +-----+------+
              v              v
            +------------------+
            |    generator     | ---> END
            +------------------+
"""
from langgraph.graph import END, START, StateGraph

from app.agent.edges import route_after_analyzer, route_after_retriever
from app.agent.nodes.analyzer import analyzer_node
from app.agent.nodes.generator import generator_node
from app.agent.nodes.retriever import retriever_node
from app.agent.nodes.web_search import web_search_node
from app.agent.state import AgentState


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("analyzer", analyzer_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("generator", generator_node)

    graph.add_edge(START, "analyzer")
    graph.add_conditional_edges(
        "analyzer",
        route_after_analyzer,
        {"retriever": "retriever", "web_search": "web_search", "generator": "generator"},
    )
    graph.add_conditional_edges(
        "retriever",
        route_after_retriever,
        {"generator": "generator", "web_search": "web_search"},
    )
    graph.add_edge("web_search", "generator")
    graph.add_edge("generator", END)

    return graph.compile()


rag_graph = build_graph()
