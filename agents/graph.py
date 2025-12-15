"""
LangGraph definition 
"""

from langgraph.graph import StateGraph, END
from .state import ComplianceState
from .nodes import (
    extract_features,
    select_next_feature,
    search_kb,
    evaluate_kb,
    search_web,
    determine_compliance,
    generate_report
)


def should_search_web(state: ComplianceState) -> str:
    """Decide whether to search web or go straight to compliance check"""
    if state.get("kb_sufficient"):
        return "determine_compliance"
    else:
        return "search_web"


def has_more_features(state: ComplianceState) -> str:
    """Check if there are more features to process"""
    if state.get("current_feature") is None:
        return "generate_report"
    else:
        return "search_kb"


def build_graph() -> StateGraph:
    """Build the compliance checking graph"""
    
    # Create graph
    graph = StateGraph(ComplianceState)
    
    # Add nodes
    graph.add_node("extract_features", extract_features)
    graph.add_node("select_next_feature", select_next_feature)
    graph.add_node("search_kb", search_kb)
    graph.add_node("evaluate_kb", evaluate_kb)
    graph.add_node("search_web", search_web)
    graph.add_node("determine_compliance", determine_compliance)
    graph.add_node("generate_report", generate_report)
    
    # Set entry point
    graph.set_entry_point("extract_features")
    
    # Add edges
    graph.add_edge("extract_features", "select_next_feature")
    
    # Conditional: do we have features to check?
    graph.add_conditional_edges(
        "select_next_feature",
        has_more_features,
        {
            "search_kb": "search_kb",
            "generate_report": "generate_report"
        }
    )
    
    graph.add_edge("search_kb", "evaluate_kb")
    
    # Conditional: is KB sufficient or need web search?
    graph.add_conditional_edges(
        "evaluate_kb",
        should_search_web,
        {
            "determine_compliance": "determine_compliance",
            "search_web": "search_web"
        }
    )
    
    graph.add_edge("search_web", "determine_compliance")
    
    # After compliance check, loop back to check more features
    graph.add_edge("determine_compliance", "select_next_feature")
    
    # End after report
    graph.add_edge("generate_report", END)
    
    return graph.compile()


# Create the runnable graph
compliance_graph = build_graph()