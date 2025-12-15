"""
State definition for the Compliance Drift Detector graph
"""

from typing import TypedDict, Annotated
from operator import add


class Finding(TypedDict):
    """A single compliance finding"""
    feature: str
    plan_value: str
    regulation: str
    source: str
    status: str  # "compliant", "gap", "needs_review"
    notes: str
    links: list[dict]


class ComplianceState(TypedDict):
    """State that flows through the graph"""
    
    # Input
    pdf_text: str
    
    # Extracted from plan
    extracted_features: dict
    
    # Processing
    features_to_check: list[str]
    current_feature: str
    current_feature_value: str
    
    # Knowledge base results
    kb_results: str
    kb_sufficient: bool
    
    # Web search results
    web_results: str
    
    # Findings accumulate
    findings: Annotated[list[Finding], add]
    
    # Final output
    report: str
    risk_level: str  # "low", "medium", "high"