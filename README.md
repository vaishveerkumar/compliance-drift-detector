# 🛡️ Compliance Drift Detector

**Compliance Drift Detector** is an AI-powered regulatory auditing system that analyzes 401(k) plan documents and evaluates feature-level compliance using an **agentic LangGraph pipeline**, an **internal Pinecone-backed knowledge base**, and a **restricted official-source web search** (DuckDuckGo).

The goal is **explainable compliance checks**: every conclusion is tied to evidence and sources.

---

## What it does

1. Ingests a 401(k) plan document (SPD / PDF)
2. Extracts structured plan features (eligibility, vesting, contributions, etc.)
3. Evaluates each extracted feature against:
   - **Internal Knowledge Base** (Pinecone retrieval), and if insufficient:
   - **Official Government Sources** via **DuckDuckGo web search** restricted to allowed domains
4. Produces:
   - Feature-by-feature outcomes (**Compliant / Gap / Needs Review**)
   - Evidence links (official URLs)
   - Final report + risk summary

---

## Tech stack

### Core application
- **Streamlit** — UI (upload, preview, modal/console, results tabs)
- **LangGraph** — Agentic architecture + stateful execution graph
- **LangChain + OpenAI** — LLM calls for extraction, sufficiency checks, and decisions

### Internal knowledge base (RAG)
- **IRS website scraping** → text extraction → **chunking**
- **Pinecone** — vector index storage
- Retrieval: **Top K = 5** chunks returned per query (configurable)

### Web verification
- **DuckDuckGo search** (via `ddgs` / `duckduckgo_search`)
- Strict domain filtering to **official sites only**:
  - `irs.gov`, `dol.gov`, `ecfr.gov`, `federalregister.gov`, `congress.gov`, `govinfo.gov`

### Reporting & visualization
- **Plotly** — charts (summary/compliance breakdown)
- **ReportLab** — PDF export

---

## Agentic architecture (LangGraph)

The system is implemented as a **LangGraph StateGraph**, where each node is a specialized agent with a single responsibility.

### Agents (nodes)

1. **Document Reader** (`extract_features`)
   - Extracts structured plan fields from the PDF text via LLM
   - Produces:
     - `extracted_features`
     - `features_to_check` (a filtered list of features that were actually found)

2. **Audit Conductor** (`select_next_feature`)
   - Orchestrates the pipeline by selecting the next feature to evaluate
   - Sets:
     - `current_feature`
     - `current_feature_value`

3. **Policy Librarian** (`search_kb`)
   - Queries the internal Pinecone knowledge base using feature-specific queries
   - Returns:
     - `kb_results` (top-k retrieved chunks)

4. **Evidence Judge** (`evaluate_kb`)
   - Determines whether KB results are sufficient to make a compliance decision
   - Sets:
     - `kb_sufficient = True/False`

5. **Regulation Researcher** (`search_web`)
   - Runs restricted web search if `kb_sufficient == False`
   - Returns:
     - `web_links` (structured list of `{title, url, snippet}`)
     - `web_results` (text summary form for the decision prompt)

6. **Compliance Decision Engine** (`determine_compliance`)
   - Uses KB evidence + web evidence (if present)
   - Produces a structured finding:
     - `status`: compliant / gap / needs_review
     - `regulation`: rule reference
     - `notes`: reasoning
     - `links`: official URLs used (when web search occurred)

7. **Report Writer** (`generate_report`)
   - Aggregates findings and generates the final report + risk classification
   - Risk level example logic:
     - High: 2+ gaps
     - Medium: 1 gap or multiple review items
     - Low: otherwise

---

## How the graph flows

**Graph loop per feature**
- `extract_features`
- `select_next_feature`
- `search_kb`
- `evaluate_kb`
  - if sufficient → `determine_compliance`
  - else → `search_web` → `determine_compliance`
- loops back to `select_next_feature`
- when no features remain → `generate_report` → END

---

## Extracted features (what the system tries to pull)

### Plan metadata
- `plan_name`
- `effective_date`

### Eligibility
- `eligibility.age_requirement`
- `eligibility.service_requirement`
- `eligibility.entry_dates`

### Contributions
- `contributions.employer_match_formula`
- `contributions.match_cap`
- `contributions.catch_up_allowed`

### Vesting
- `vesting.type`
- `vesting.schedule`
- `vesting.years_to_full`

### Auto-enrollment
- `auto_enrollment.enabled`
- `auto_enrollment.default_rate`
- `auto_enrollment.auto_escalation`

### Distributions
- `distributions.hardship_allowed`
- `distributions.loans_allowed`

**Important:** Only fields that are successfully extracted and non-null are added to `features_to_check`.

---

## Internal Knowledge Base details

The internal KB is built by:
- Scraping IRS guidance pages (and related official pages as needed)
- Cleaning + converting to text
- Chunking into retrievable passages
- Embedding + storing in **Pinecone**

Retrieval behavior:
- Each feature maps to a query (e.g., `vesting schedule requirements`)
- The system retrieves **Top 5** chunks from Pinecone per query

---

## Web search details

Web verification is only triggered if:
- The Evidence Judge marks KB evidence as insufficient (`kb_sufficient = False`)

Search engine:
- DuckDuckGo (DDGS)

Restrictions:
- Search results are filtered to **only** allowed official domains

Returned fields per result:
- `title` — page title
- `url` — official link
- `snippet` — short summary text from the search provider

---

## Running locally

### Requirements
- Python 3.10+
- OpenAI API key
- Pinecone credentials (if your KB retrieval is enabled)

### Install
```bash
pip install -r requirements.txt
