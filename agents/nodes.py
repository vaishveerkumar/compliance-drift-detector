"""
Agent nodes for the Compliance Drift Detector graph
"""

import json
from langchain_openai import ChatOpenAI
from .state import ComplianceState, Finding
from tools import search_knowledge_base, search_official_sources

# Initialize LLM
llm = ChatOpenAI(model="gpt-5-nano", temperature=2)


# ============================================================
# NODE 1: Extract Features from Plan Document
# ============================================================

EXTRACTION_PROMPT = """You are an expert at extracting structured data from 401(k) plan documents.

Extract the following features from this plan document. Return ONLY valid JSON.

{{
  "plan_name": "string or null",
  "effective_date": "string or null",
  
  "eligibility": {{
    "age_requirement": "number or null",
    "service_requirement": "string or null",
    "entry_dates": "string or null"
  }},
  
  "contributions": {{
    "employer_match_formula": "string or null",
    "match_cap": "string or null",
    "catch_up_allowed": "boolean or null"
  }},
  
  "vesting": {{
    "type": "string or null (immediate, cliff, graded)",
    "schedule": "string or null",
    "years_to_full": "number or null"
  }},
  
  "auto_enrollment": {{
    "enabled": "boolean or null",
    "default_rate": "number or null",
    "auto_escalation": "boolean or null"
  }},
  
  "distributions": {{
    "hardship_allowed": "boolean or null",
    "loans_allowed": "boolean or null"
  }}
}}

PLAN DOCUMENT:
{pdf_text}
"""


def extract_features(state: ComplianceState) -> dict:
    """Extract plan features using LLM"""
    
    prompt = EXTRACTION_PROMPT.format(pdf_text=state["pdf_text"][:50000])
    
    response = llm.invoke(prompt)
    content = response.content.strip()
    
    # Clean markdown if present
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    
    features = json.loads(content.strip())
    
    # Build list of features to check
    features_to_check = []
    
    if features.get("eligibility", {}).get("age_requirement"):
        features_to_check.append("eligibility_age")
    if features.get("eligibility", {}).get("service_requirement"):
        features_to_check.append("eligibility_service")
    if features.get("vesting", {}).get("type"):
        features_to_check.append("vesting")
    if features.get("contributions", {}).get("employer_match_formula"):
        features_to_check.append("employer_match")
    if features.get("auto_enrollment", {}).get("enabled") is not None:
        features_to_check.append("auto_enrollment")
    if features.get("contributions", {}).get("catch_up_allowed") is not None:
        features_to_check.append("catch_up")
    
    return {
        "extracted_features": features,
        "features_to_check": features_to_check,
        "findings": []
    }


# ============================================================
# NODE 2: Select Next Feature to Check
# ============================================================

def select_next_feature(state: ComplianceState) -> dict:
    """Pick the next feature to verify"""
    
    features = state.get("features_to_check", [])
    extracted = state.get("extracted_features", {})
    
    if not features:
        return {"current_feature": None, "current_feature_value": None, "features_to_check": [] }
    
    feature = features[0]
    remaining = features[1:]
    
    # Get the value for this feature
    value = None
    if feature == "eligibility_age":
        value = str(extracted.get("eligibility", {}).get("age_requirement"))
    elif feature == "eligibility_service":
        value = extracted.get("eligibility", {}).get("service_requirement")
    elif feature == "vesting":
        vesting = extracted.get("vesting", {})
        value = f"{vesting.get('type')} - {vesting.get('schedule', 'N/A')}"
    elif feature == "employer_match":
        value = extracted.get("contributions", {}).get("employer_match_formula")
    elif feature == "auto_enrollment":
        auto = extracted.get("auto_enrollment", {})
        value = f"Enabled: {auto.get('enabled')}, Rate: {auto.get('default_rate')}%"
    elif feature == "catch_up":
        value = str(extracted.get("contributions", {}).get("catch_up_allowed"))
    
    return {
        "current_feature": feature,
        "current_feature_value": value,
        "features_to_check": remaining
    }


# ============================================================
# NODE 3: Search Knowledge Base
# ============================================================

FEATURE_QUERIES = {
    "eligibility_age": "401k plan maximum age requirement eligibility ERISA",
    "eligibility_service": "401k plan maximum service requirement eligibility years",
    "vesting": "401k vesting schedule requirements cliff graded maximum years ERISA",
    "employer_match": "401k employer matching contribution requirements safe harbor",
    "auto_enrollment": "401k automatic enrollment requirements SECURE 2.0 2025",
    "catch_up": "401k catch-up contribution limits age 50 SECURE 2.0"
}


def search_kb(state: ComplianceState) -> dict:
    """Search knowledge base for relevant regulations"""
    
    feature = state["current_feature"]
    query = FEATURE_QUERIES.get(feature, feature)
    
    results = search_knowledge_base(query, top_k=3)
    
    return {"kb_results": results}


# ============================================================
# NODE 4: Evaluate KB Results
# ============================================================

EVAL_PROMPT = """You are a compliance expert evaluating if knowledge base results answer the question.

Feature being checked: {feature}
Plan value: {plan_value}

Knowledge base results:
{kb_results}

Question: Do these results provide enough information to determine if the plan value is compliant?

Respond with ONLY "sufficient" or "insufficient".
"""


def evaluate_kb(state: ComplianceState) -> dict:
    """Evaluate if KB results are sufficient"""
    
    prompt = EVAL_PROMPT.format(
        feature=state["current_feature"],
        plan_value=state["current_feature_value"],
        kb_results=state["kb_results"]
    )
    
    response = llm.invoke(prompt)
    is_sufficient = response.content.strip().lower() == "sufficient"

    return {"kb_sufficient": is_sufficient}


# ============================================================
# NODE 5: Search Web (only if KB insufficient)
# ============================================================

def search_web(state: ComplianceState) -> dict:
    """Search official government sources"""
    feature = state["current_feature"]
    query = FEATURE_QUERIES.get(feature, feature) + " 2024 2025"

    links = search_official_sources(query, max_results=3)

    # keep both: structured links for UI + text version for the LLM
    web_text = "\n".join([f"- {l.get('title')}: {l.get('url')}" for l in links if l.get("url")])

    return {
        "web_links": links,      
        "web_results": web_text  
    }

# ============================================================
# NODE 6: Make Compliance Determination
# ============================================================

COMPLIANCE_PROMPT = """You are a 401(k) compliance expert. Determine if the plan feature is compliant.

Feature: {feature}
Plan Value: {plan_value}

Regulations Found:
{regulations}

Based on the regulations, is this plan feature compliant?

Respond in this exact JSON format:
{{
  "status": "compliant" or "gap" or "needs_review",
  "regulation": "the specific rule that applies",
  "notes": "brief explanation"
}}
"""


def determine_compliance(state: ComplianceState) -> dict:
    """Determine if feature is compliant"""
    
    # Combine KB and web results
    regulations = state.get("kb_results", "")
    if state.get("web_results"):
        regulations += "\n\n" + state["web_results"]
    
    prompt = COMPLIANCE_PROMPT.format(
        feature=state["current_feature"],
        plan_value=state["current_feature_value"],
        regulations=regulations
    )
    
    response = llm.invoke(prompt)
    content = response.content.strip()
    
    # Clean markdown
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    
    result = json.loads(content.strip())
    
    finding = Finding(
        feature=state["current_feature"],
        plan_value=state["current_feature_value"],
        regulation=result.get("regulation", ""),
        source="Web Search",
        status=result.get("status", "needs_review"),
        notes=result.get("notes", ""),
        links=state.get("web_links", [])
    )

    return {"findings": [finding]}


# ============================================================
# NODE 7: Generate Final Report
# ============================================================

REPORT_PROMPT = """You are a compliance report writer. Generate a clear, professional compliance report.

Plan Name: {plan_name}

Findings:
{findings}

Generate a compliance report with:
1. Executive Summary (2-3 sentences)
2. Compliant Items (list with ✓)
3. Gaps Found (list with ✗)  
4. Items Needing Review (list with ⚠)
5. Overall Risk Level (Low/Medium/High)
6. Recommended Actions

Be concise but thorough.
"""


def generate_report(state: ComplianceState) -> dict:
    """Generate the final compliance report"""
    
    plan_name = state.get("extracted_features", {}).get("plan_name", "Unknown Plan")
    
    # Format findings
    findings_text = ""
    for f in state.get("findings", []):
        findings_text += f"""
Feature: {f['feature']}
Plan Value: {f['plan_value']}
Status: {f['status']}
Regulation: {f['regulation']}
Source: {f['source']}
Notes: {f['notes']}
---
"""
    
    prompt = REPORT_PROMPT.format(
        plan_name=plan_name,
        findings=findings_text
    )
    
    response = llm.invoke(prompt)
    
    # Determine risk level
    gaps = [f for f in state.get("findings", []) if f["status"] == "gap"]
    reviews = [f for f in state.get("findings", []) if f["status"] == "needs_review"]
    
    if len(gaps) >= 2:
        risk = "High"
    elif len(gaps) == 1 or len(reviews) >= 2:
        risk = "Medium"
    else:
        risk = "Low"
    
    return {
        "report": response.content,
        "risk_level": risk
    }