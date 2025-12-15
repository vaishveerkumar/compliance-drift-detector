# 🛡️ Compliance Drift Detector

**An agentic AI system that audits 401(k) plan documents against current IRS and DOL regulations, catching compliance gaps before auditors do.**

---

## The Problem

401(k) plans don't fail audits overnight. They drift out of compliance slowly as regulations evolve (SECURE Act, SECURE 2.0, DOL updates) and plan documents lag behind. By the time an auditor catches it, employers face penalties, employees face uncertainty, and nobody wins.

## The Solution

This system acts as a proactive compliance layer. Upload a plan document, and the AI agents will extract key provisions, verify them against current regulations, and generate an audit-ready report complete with risk scores and regulatory citations.

---

## ✨ Key Features

**Agentic Architecture**  
Built on LangGraph to orchestrate stateful LLM agents that extract, verify, and adjudicate plan rules autonomously.

**Hybrid RAG Pipeline**  
Combines Pinecone vector storage with semantic retrieval and restricted web verification limited to official IRS, DOL, eCFR, and Federal Register domains.

**End-to-End Document Intelligence**  
Converts unstructured plan PDFs into structured compliance findings, risk assessments, and regulatory citations.

**Real-Time Execution Tracing**  
Streamlit interface shows exactly what each agent is doing, building trust through transparency.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI                             │
│              Upload PDF → View Agent Trace → Download Report    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LANGGRAPH ORCHESTRATOR                     │
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│   │ Extract  │───▶│ Research │───▶│Adjudicate│───▶│  Report   │
│   │ Features │    │ Regulations   │ Compliance│    │Generator   │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                         │                                       │
│                         ▼                                       │
│              ┌─────────────────────┐                            │
│              │   KB Sufficient?    │                            │
│              │    Yes / No         │                            │
│              └──────────┬──────────┘                            │
│                         │ No                                    │
│                         ▼                                       │
│              ┌─────────────────────┐                            │
│              │  Web Verification   │                            │
│              │  (IRS/DOL/eCFR)     │                            │
│              └─────────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                │
│                                                                 │
│   ┌─────────────────┐              ┌─────────────────────────┐  │
│   │    Pinecone     │              │   Restricted Web Search │  │
│   │  Vector Store   │              │   • irs.gov             │  │
│   │                 │              │   • dol.gov             │  │
│   │  Regulation KB  │              │   • ecfr.gov            │  │
│   │  (Pre-embedded) │              │   • federalregister.gov │  │
│   └─────────────────┘              └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|------------|
| Orchestration | LangGraph |
| LLM | OpenAI GPT-5 |
| Vector Store | Pinecone |
| Embeddings | Sentence Transformers |
| Web Search | DuckDuckGo API (domain-restricted) |
| Frontend | Streamlit |
| PDF Processing | PyPDF2 |

---

## 📁 Project Structure

```
compliance-drift-detector/
├── app.py                    # Streamlit frontend
├── agents/
│   ├── __init__.py
│   ├── graph.py              # LangGraph workflow definition
│   ├── nodes.py              # Agent node implementations
│   └── state.py              # State schema
├── tools/
│   ├── __init__.py
│   ├── pdf_extractor.py      # PDF to text conversion
│   ├── pinecone_search.py    # Knowledge base retrieval
│   └── web_search.py         # Restricted domain search
├── .env.example              # Environment variable template
└── requirements.txt          # Dependencies
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- OpenAI API key
- Pinecone API key

### Installation

```bash
# Clone the repository
git clone https://github.com/vaishveerkumar/compliance-drift-detector.git
cd compliance-drift-detector

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Add your API keys to .env
```

### Running the Application

```bash
streamlit run app.py
```

Navigate to `http://localhost:8501` in your browser.

---

## 💡 How It Works

1. **Upload** a 401(k) plan document (PDF)
2. **Extract** agent identifies key provisions (contribution limits, vesting schedules, eligibility rules)
3. **Research** agent queries the regulation knowledge base via semantic search
4. **Verify** agent checks against live regulatory sources if KB coverage is insufficient
5. **Adjudicate** agent determines compliance status for each provision
6. **Report** agent generates audit-ready findings with risk scores and citations

---

## 📋 Compliance Areas Covered

- Contribution limits (employee deferrals, employer match, catch-up contributions)
- Vesting schedules (cliff, graded, SECURE 2.0 requirements)
- Eligibility requirements (age, service, LTPT employees)
- Safe harbor provisions
- Required minimum distributions
- Hardship withdrawal rules
- Nondiscrimination testing requirements

---

## 🎯 Sample Output

```
COMPLIANCE AUDIT REPORT
=======================
Document: Acme Corp 401(k) Plan Document
Analysis Date: December 2025

FINDING #1: Vesting Schedule Non-Compliance
Status: ⚠️ REQUIRES ATTENTION
Risk Level: Medium

Issue: Plan document specifies 7-year graded vesting schedule.
Regulation: SECURE 2.0 Act requires maximum 3-year cliff or 
           2-to-6-year graded vesting for employer contributions.
Citation: SECURE 2.0 Act Section 301, effective plan years 
          beginning after December 31, 2024

Recommendation: Amend vesting schedule to comply with new maximums.

