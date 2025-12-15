"""
Compliance Drift Detector - Streamlit App

"""

import time
import html
import base64
from datetime import datetime
from io import BytesIO
from typing import Optional, List, Dict, Any
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
import plotly.graph_objects as go
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from agents import compliance_graph
from tools import extract_text_from_pdf

# Load env
load_dotenv()

# ============================================================
# Page config & CSS
# ============================================================
st.set_page_config(
    page_title="Compliance Drift Detector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

STYLING_CSS = """
<style>
  [data-testid="stAppViewContainer"] {
    background-color: #050505;
    background-image: radial-gradient(at 50% 0%, #1a1a2e 0%, #050505 60%);
    color: #e0e0e0;
  }

  [data-testid="stSidebar"] {
    background-color: #0a0a0a;
    border-right: 1px solid #1f1f1f;
  }

  h1, h2, h3 {
    font-family: 'Inter', sans-serif;
    color: #ffffff;
    font-weight: 700;
    letter-spacing: -0.5px;
  }

  .glass-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    margin-bottom: 20px;
  }

  .report-header {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 18px 22px;
  }

  .chip {
    padding: 4px 10px;
    border-radius: 999px;
    font-weight: 800;
    letter-spacing: 0.04em;
    border: 1px solid rgba(255,255,255,0.08);
    font-size: 0.8rem;
    display: inline-block;
    margin-left: 8px;
  }

  div.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    transition: all 0.2s ease;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3);
  }
  div.stButton > button:hover {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
  }
  div.stButton > button:active { transform: translateY(1px); }

  .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; }
  .stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 6px;
    color: #9ca3af;
    padding: 8px 16px;
  }
  .stTabs [aria-selected="true"] {
    background-color: rgba(139, 92, 246, 0.1) !important;
    color: #c4b5fd !important;
    border: 1px solid rgba(139, 92, 246, 0.3);
  }

  .streamlit-expanderHeader {
    background-color: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 8px;
    color: #e5e7eb;
  }

  [data-baseweb="file-uploader"] {
    background: rgba(255,255,255,0.02);
    border: 1px dashed rgba(255,255,255,0.2);
    border-radius: 12px;
    padding: 20px;
  }
</style>
"""
st.markdown(STYLING_CSS, unsafe_allow_html=True)


# ============================================================
# Modal CSS (agent console)
# ============================================================
MODAL_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');

  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.7);
    z-index: 100000;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    backdrop-filter: blur(4px);
  }

  .console {
    width: min(820px, 92vw);
    border: 1px solid rgba(139, 92, 246, 0.3);
    background: #0f0f11;
    border-radius: 16px;
    box-shadow: 0 0 40px rgba(139, 92, 246, 0.15);
    padding: 24px;
    pointer-events: auto;
    font-family: 'Inter', sans-serif;
    animation: pop 220ms cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
  }

  .console::before {
    content: "";
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }

  .console-content { position: relative; z-index: 2; }

  @keyframes pop {
    from { transform: scale(0.95) translateY(10px); opacity: 0; }
    to   { transform: scale(1) translateY(0); opacity: 1; }
  }

  .console-top {
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom: 16px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 12px;
  }

  .console-title {
    font-weight: 800;
    font-size: 1.1rem;
    color: #fff;
    display:flex;
    align-items:center;
    gap: 12px;
  }

  .badge {
    font-size: 0.7rem;
    padding: 4px 10px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  .badge-live { background: rgba(139, 92, 246, 0.15); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.3); box-shadow: 0 0 10px rgba(139,92,246,0.2); }
  .badge-done { background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.3); }
  .badge-warn { background: rgba(245, 158, 11, 0.15); color: #fcd34d; border: 1px solid rgba(245, 158, 11, 0.3); }

  .stage {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 14px;
  }

  .stage-name {
    font-weight: 900;
    font-size: 1.15rem;
    margin-bottom: 6px;
    background: linear-gradient(90deg, #fff, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .stage-desc {
    color: #9ca3af;
    font-size: 0.95rem;
    line-height: 1.5;
  }

  .rail { display:flex; gap: 6px; margin-top: 14px; }
  .dot {
    height: 4px;
    flex-grow: 1;
    background: rgba(255,255,255,0.1);
    border-radius: 2px;
    transition: background 0.3s;
  }
  .dot-on { background: #8b5cf6; box-shadow: 0 0 8px #8b5cf6; }

  .mini-list {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    height: 140px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    margin-top: 8px;
  }

  .mini-item {
    padding: 6px 0;
    border-bottom: 1px solid rgba(255,255,255,0.03);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .mini-ok   { color: #6ee7b7; }
  .mini-warn { color: #fcd34d; }
  .mini-bad  { color: #f43f5e; }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
</style>
"""


# ============================================================
# Helpers
# ============================================================
def show_pdf(file_bytes: bytes):
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="500" '
        f'style="border-radius:12px; border:1px solid #333;"></iframe>',
        unsafe_allow_html=True,
    )


def markdown_to_simple_pdf_bytes(title: str, markdown_text: str) -> bytes:
    """
    NOTE: This renders Markdown as plain text (no bold/italics).
    If you want true Markdown styling in PDF, we'd switch to an HTML->PDF approach.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    x = 50
    y = height - 60
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, title)
    y -= 26
    c.setFont("Helvetica", 10)
    max_chars = 105

    for line in markdown_text.splitlines():
        if y < 60:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)
        line = line.replace("\t", "    ")
        chunks = [line[i : i + max_chars] for i in range(0, len(line), max_chars)] or [""]
        for ch in chunks:
            if y < 60:
                c.showPage()
                y = height - 60
                c.setFont("Helvetica", 10)
            c.drawString(x, y, ch)
            y -= 12

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# Agent / Stage setup
# ============================================================
STAGE_ORDER = [
    "extract_features",
    "search_kb",
    "evaluate_kb",
    "search_web",
    "determine_compliance",
    "generate_report",
]

NODE_COPY = {
    "extract_features": ("Parsing Document Structure", "Reading the plan PDF to extract key rules."),
    "select_next_feature": ("Orchestrating Logic", "Choosing the next compliance check."),
    "search_kb": ("Querying Internal Knowledge", "Looking up internal policy knowledge."),
    "evaluate_kb": ("Evaluating Evidence Strength", "Deciding whether internal evidence is enough."),
    "search_web": ("Searching Official Registers", "Verifying via official government sources."),
    "determine_compliance": ("Compliance Adjudication", "Determining pass/fail and rationale."),
    "generate_report": ("Compiling Final Artifact", "Generating an audit-ready report."),
}

AGENT_FRIENDLY = {
    "extract_features": "Document Reader",
    "select_next_feature": "Audit Conductor",
    "search_kb": "Policy Librarian",
    "evaluate_kb": "Evidence Judge",
    "search_web": "Regulation Researcher",
    "determine_compliance": "Compliance Decision Engine",
    "generate_report": "Report Writer",
}


def stage_index(node: str) -> int:
    return STAGE_ORDER.index(node) if node in STAGE_ORDER else 0


def build_console_html(
    stage_title: str,
    stage_desc: str,
    step_idx: int,
    step_total: int,
    history: list,
    badge: str,
    agent_name: str = "Agent",
    links: Optional[List[Dict[str, Any]]] = None,
) -> str:
    # Progress dots
    dots_html = "".join(
        [f'<div class="dot {"dot-on" if i <= step_idx else ""}"></div>' for i in range(step_total)]
    )

    badge = (badge or "LIVE").upper()
    badge_class = "badge-live"
    if badge == "DONE":
        badge_class = "badge-done"
    elif badge in ("REVIEW", "WARN", "ALERT"):
        badge_class = "badge-warn"

    # History
    hist_html = ""
    for h in history[-10:]:
        tone = h.get("tone", "ok")
        cls = {"ok": "mini-ok", "warn": "mini-warn", "bad": "mini-bad"}.get(tone, "mini-ok")
        hist_html += f'<div class="mini-item {cls}"><span>›</span> {html.escape(h.get("text",""))}</div>'

    # Links panel 
    links = links or []
    links_html = ""
    if links:
        items = []
        for l in links:
            t = html.escape((l.get("title") or "Source").strip())
            u = html.escape((l.get("url") or "").strip())
            if not u:
                continue
            items.append(
                f"""
                <div class="mini-item" style="border-bottom:none; padding:6px 0;">
                  <span style="opacity:0.7;">↗</span>
                  <a href="{u}" target="_blank" style="color:#c4b5fd; text-decoration:none;">
                    {t}
                  </a>
                </div>
                """
            )
        if items:
            links_html = f"""
            <div class="stage" style="margin-top:10px;">
              <div style="font-weight:900; color:#fff; margin-bottom:6px;">Web sources being searched</div>
              <div style="color:#9ca3af; font-size:0.9rem; margin-bottom:8px;">
                These links came from the restricted official web search step:
              </div>
              {''.join(items)}
            </div>
            """

    return f"""
    {MODAL_CSS}
    <div class="overlay">
      <div class="console">
        <div class="console-content">
          <div class="console-top">
            <div class="console-title">
              <span>🤖</span>
              <span>{html.escape(agent_name)}</span>
              <span class="badge {badge_class}">{html.escape(badge)}</span>
            </div>
            <div style="opacity:0.6; font-size:0.8rem; font-family:'JetBrains Mono'">PROCESS_ID: {int(time.time())}</div>
          </div>

          <div class="stage">
            <div class="stage-name">{html.escape(stage_title)}</div>
            <div class="stage-desc">{html.escape(stage_desc)}</div>
            <div class="rail">{dots_html}</div>
          </div>

          {links_html}

          <div class="mini-list">
            {hist_html}
          </div>
        </div>
      </div>
    </div>
    """


# ============================================================
# Report helpers
# ============================================================
def normalize_links(links: Optional[List[Dict[str, Any]]]) -> List[Dict[str, str]]:
    seen = set()
    out: List[Dict[str, str]] = []
    for l in (links or []):
        url = (l.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(
            {
                "title": (l.get("title") or "Official source").strip(),
                "url": url,
                "snippet": (l.get("snippet") or "").strip(),
            }
        )
    return out


def compile_report(plan_name: str, risk_level: str, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts = {"compliant": 0, "gap": 0, "needs_review": 0}
    for f in findings:
        s = f.get("status", "needs_review")
        counts[s] = counts.get(s, 0) + 1

    all_sources: List[Dict[str, str]] = []
    for f in findings:
        all_sources.extend(normalize_links(f.get("links", [])))
    all_sources = normalize_links(all_sources)

    return {
        "meta": {
            "plan_name": plan_name,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "risk_level": risk_level,
            "counts": counts,
        },
        "findings": findings,
        "sources": all_sources,
    }


def report_to_markdown(r: Dict[str, Any]) -> str:
    meta = r["meta"]
    c = meta["counts"]
    lines: List[str] = []

    lines.append(f"# Compliance Report — {meta['plan_name']}")
    lines.append(f"**Generated:** {meta['generated_at']}")
    lines.append(f"**Overall Risk:** {meta['risk_level']}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(f"- ✅ Compliant: **{c.get('compliant',0)}**")
    lines.append(f"- ❌ Gaps: **{c.get('gap',0)}**")
    lines.append(f"- ⚠ Needs Review: **{c.get('needs_review',0)}**")
    lines.append("")
    lines.append("## Findings")
    for f in r["findings"]:
        status = f.get("status", "needs_review")
        icon = {"compliant": "✅", "gap": "❌", "needs_review": "⚠"}.get(status, "⚠")
        feature = f.get("feature", "—")
        plan_value = str(f.get("plan_value", "—"))
        regulation = (f.get("regulation") or "—").replace("\n", " ")
        notes = (f.get("notes") or "").strip() or "—"
        lines.append(f"### {icon} {feature}")
        lines.append(f"- **Plan Value:** {plan_value}")
        lines.append(f"- **Regulation:** {regulation}")
        lines.append(f"- **Notes:** {notes}")
        links = normalize_links(f.get("links", []))
        if links:
            lines.append("- **Sources:**")
            for l in links:
                lines.append(f"  - [{l['title']}]({l['url']})")
        lines.append("")

    lines.append("## Appendix — All Official Sources")
    if r["sources"]:
        for l in r["sources"]:
            lines.append(f"- [{l['title']}]({l['url']})")
    else:
        lines.append("_No official web sources were used for this run._")

    return "\n".join(lines)


# ============================================================
# How it Works
# ============================================================
HOW_STEPS = [
    {
        "key": "extract_features",
        "title": "Document Reader",
        "subtitle": "Extracting plan features from the uploaded SPD/PDF",
        "detail": "Reads the PDF text and extracts structured fields like eligibility, vesting, match, auto-enroll, etc.",
    },
    {
        "key": "search_kb",
        "title": "Policy Librarian",
        "subtitle": "Searching internal knowledge base",
        "detail": "Looks up relevant guidance in your internal knowledge base for the current feature.",
    },
    {
        "key": "evaluate_kb",
        "title": "Evidence Judge",
        "subtitle": "Deciding if KB evidence is sufficient",
        "detail": "Classifies KB results as sufficient/insufficient to make a compliance call.",
    },
    {
        "key": "search_web",
        "title": "Regulation Researcher",
        "subtitle": "Searching official sources when KB is insufficient",
        "detail": "Runs restricted official web search and returns sources (title/url/snippet).",
    },
    {
        "key": "determine_compliance",
        "title": "Compliance Decision Engine",
        "subtitle": "Determining pass/fail/review",
        "detail": "Combines evidence and produces: status + regulation text + notes.",
    },
    {
        "key": "generate_report",
        "title": "Report Writer",
        "subtitle": "Generating the final report + risk level",
        "detail": "Builds the report and assigns Low/Medium/High risk based on gaps/reviews.",
    },
]

FEATURES_EXTRACTED = [
    "plan_name, effective_date",
    "eligibility: age_requirement, service_requirement, entry_dates",
    "contributions: employer_match_formula, match_cap, catch_up_allowed",
    "vesting: type, schedule, years_to_full",
    "auto_enrollment: enabled, default_rate, auto_escalation",
    "distributions: hardship_allowed, loans_allowed",
]


def build_how_it_works_html() -> str:
    
    steps_js = [
        {"title": s["title"], "subtitle": s["subtitle"], "detail": s["detail"], "key": s["key"]}
        for s in HOW_STEPS
    ]

    return f"""
    <style>
      .how-wrap {{
        font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial;
        color: #e5e7eb;
      }}
      .how-top {{
        display:flex; align-items:center; justify-content:space-between;
        padding: 14px 16px; border-radius: 14px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 12px;
      }}
      .how-title {{
        font-weight: 950; letter-spacing: 0.10em;
        font-size: 1.05rem;
      }}
      .how-sub {{
        font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
        font-size: 0.75rem; opacity: 0.7; margin-top: 4px;
      }}

      .pipeline {{
        display:flex; gap: 12px; align-items:center;
        padding: 10px 8px; margin-bottom: 14px;
      }}

      .node {{
        width: 74px; height: 74px; border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.02);
        display:flex; flex-direction:column; align-items:center; justify-content:center;
        position: relative;
        transition: all .25s ease;
        user-select: none;
      }}
      .node .label {{
        font-size: .62rem; margin-top: 6px; opacity: .8;
        text-transform: uppercase;
        letter-spacing: .06em;
      }}

      .node.done {{
        border-color: rgba(139,92,246,0.40);
        box-shadow: 0 0 14px rgba(139,92,246,0.15);
      }}

      .node.active {{
        border-color: rgba(139,92,246,0.80);
        box-shadow: 0 0 28px rgba(139,92,246,0.45);
        animation: pulse 1.4s ease-in-out infinite;
        transform: translateY(-2px);
      }}

      @keyframes pulse {{
        0%   {{ transform: translateY(-2px) scale(1); }}
        50%  {{ transform: translateY(-2px) scale(1.04); }}
        100% {{ transform: translateY(-2px) scale(1); }}
      }}

      .connector {{
        position: relative;
        height: 2px;
        flex: 1;
        background: rgba(255,255,255,0.08);
        overflow: hidden;
        border-radius: 2px;
      }}

      .connector::after {{
        content: "";
        position: absolute;
        left: -40%;
        top: 0;
        width: 40%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(139,92,246,0.95), transparent);
        opacity: 0;
      }}

      .connector.flow::after {{
        animation: flow 1.1s linear infinite;
        opacity: 1;
      }}

      @keyframes flow {{
        from {{ left: -40%; }}
        to   {{ left: 100%; }}
      }}

      .panel {{
        display:grid;
        grid-template-columns: 1.2fr 1fr;
        gap: 14px;
      }}
      .card {{
        border-radius: 16px;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 16px;
        min-height: 220px;
      }}
      .card h3 {{
        margin: 0 0 6px 0; font-size: 1rem; font-weight: 900;
      }}
      .card .muted {{
        color: #9ca3af; font-size: .9rem; line-height: 1.45;
      }}
      .chip {{
        display:inline-block;
        padding: 4px 10px; border-radius: 999px;
        border: 1px solid rgba(139,92,246,0.35);
        background: rgba(139,92,246,0.10);
        color: #c4b5fd;
        font-family: "JetBrains Mono", monospace;
        font-size: .72rem;
        margin-left: 10px;
      }}
      ul {{
        margin: 10px 0 0 18px;
        padding: 0;
        color:#cbd5e1;
        font-size: .9rem;
        line-height: 1.45;
      }}
      .controls {{
        display:flex; gap: 10px; margin-top: 14px; align-items:center;
      }}
      .btn {{
        user-select:none;
        border-radius: 12px;
        padding: 10px 14px;
        border: 1px solid rgba(255,255,255,0.12);
        background: rgba(255,255,255,0.04);
        cursor:pointer;
        font-weight: 800;
        transition: all .2s ease;
      }}
      .btn:hover {{
        border-color: rgba(139,92,246,0.6);
        box-shadow: 0 0 18px rgba(139,92,246,0.18);
      }}
      .statusline {{
        font-family: "JetBrains Mono", monospace;
        font-size: .85rem;
        color: #6ee7b7;
        margin-top: 10px;
        opacity: 0.9;
      }}
    </style>

    <div class="how-wrap">
      <div class="how-top">
        <div>
          <div class="how-title">HOW IT WORKS</div>
          <div class="how-sub">LangGraph pipeline • step-by-step execution</div>
        </div>
        <div class="chip" id="chipKey">extract_features</div>
      </div>

      <div class="pipeline" id="pipe"></div>

      <div class="panel">
        <div class="card">
          <h3 id="stepTitle">Document Reader</h3>
          <div class="muted" id="stepSub">Extracting plan features from the uploaded SPD/PDF</div>
          <div class="statusline" id="statusLine">&gt;&gt; Booting pipeline…</div>
          <div style="margin-top:10px" class="muted" id="stepDetail">
            Reads the PDF text and extracts structured fields like eligibility, vesting, match, auto-enroll, etc.
          </div>

          <div class="controls">
            <div class="btn" id="prevBtn">◀ Prev</div>
            <div class="btn" id="playBtn">▶ Play</div>
            <div class="btn" id="nextBtn">Next ▶</div>
          </div>
        </div>

        <div class="card">
          <h3>Features extracted</h3>
          <div class="muted">These are the structured fields the Document Reader tries to pull from the PDF:</div>
          <ul>
            {"".join([f"<li>{html.escape(x)}</li>" for x in FEATURES_EXTRACTED])}
          </ul>
        </div>
      </div>
    </div>

    <script>
      const steps = {steps_js};
      const pipe = document.getElementById("pipe");

      function iconFor(key){{
        if(key==="extract_features") return "📄";
        if(key==="search_kb") return "📚";
        if(key==="evaluate_kb") return "⚖️";
        if(key==="search_web") return "🌐";
        if(key==="determine_compliance") return "✅";
        if(key==="generate_report") return "🧾";
        return "•";
      }}

      function renderPipe(activeIdx){{
        pipe.innerHTML = "";
        steps.forEach((s, i) => {{
          const node = document.createElement("div");
          let cls = "node";
          if (i < activeIdx) cls += " done";
          if (i === activeIdx) cls += " active";
          node.className = cls;

          node.innerHTML = `
            <div style="font-size:1.4rem">${{iconFor(s.key)}}</div>
            <div class="label">${{s.key.replaceAll("_"," ")}}</div>
          `;

          pipe.appendChild(node);

          if (i < steps.length - 1) {{
            const conn = document.createElement("div");
            conn.className = "connector";
            if (i === activeIdx - 1) conn.classList.add("flow");
            pipe.appendChild(conn);
          }}
        }});
      }}

      let idx = 0;
      let timer = null;

      function setStep(i){{
        idx = (i + steps.length) % steps.length;
        const s = steps[idx];

        // show flow first
        renderPipe(idx);

        // then update text with a small delay (feels like execution)
        setTimeout(() => {{
          document.getElementById("stepTitle").textContent = s.title;
          document.getElementById("stepSub").textContent = s.subtitle;
          document.getElementById("stepDetail").textContent = s.detail;
          document.getElementById("chipKey").textContent = s.key;
          document.getElementById("statusLine").textContent = `>> Executing: ${{s.key}} …`;
        }}, 280);
      }}

      function play(){{
        if(timer) return;
        document.getElementById("playBtn").textContent = "⏸ Pause";
        timer = setInterval(() => {{
          setStep(idx + 1);
        }}, 1400);
      }}

      function pause(){{
        if(!timer) return;
        clearInterval(timer);
        timer = null;
        document.getElementById("playBtn").textContent = "▶ Play";
      }}

      document.getElementById("prevBtn").onclick = () => {{ pause(); setStep(idx-1); }};
      document.getElementById("nextBtn").onclick = () => {{ pause(); setStep(idx+1); }};
      document.getElementById("playBtn").onclick = () => {{ timer ? pause() : play(); }};

      setStep(0);
    </script>
    """


@st.dialog("How it works", width="large")
def how_it_works_dialog():
    components.html(build_how_it_works_html(), height=560, scrolling=False)


# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ System Control")
    st.markdown(
        """
        <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; margin-bottom:20px;">
            <small style="color:#aaa;">STATUS</small><br>
            <span style="color:#4ade80; font-weight:bold;">● SYSTEM ONLINE</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 📖 About")
    st.info("**Compliance Drift Detector** uses autonomous AI agents to audit 401(k) plans against IRS/DOL guidance.")

    st.markdown("---")
    demo_mode = st.toggle("🎬 Cinematic Mode", value=True)
    demo_delay = st.slider("Simulation Latency (s)", 0.0, 1.0, 0.25, 0.05) if demo_mode else 0.0
    st.markdown("---")
    st.caption("v2.4.0 • Built with LangGraph")


# ============================================================
# Main header
# ============================================================
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Compliance Drift Detector")
    st.markdown(
        "<h4 style='color:#8b5cf6; margin-top:-20px; margin-bottom: 18px;'>AI-Powered Regulatory Auditing System</h4>",
        unsafe_allow_html=True,
    )
with col2:
    right_a, right_b = st.columns([1, 1])
    with right_a:
        if st.button("ℹ️ How it works", use_container_width=True):
            how_it_works_dialog()
    with right_b:
        st.markdown(
            """
            <div style="text-align:right; font-family:'JetBrains Mono'; opacity:0.5; font-size:0.8rem;">
            SECURE_CONN_ESTABLISHED<br>
            <span style="color:#8b5cf6">ENCRYPTION: AES-256</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# Upload Section
# ============================================================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "📂 Upload Plan Document (SPD/PDF)",
    type=["pdf"],
    help="Upload a Summary Plan Description (SPD) or Plan Document",
)
st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# Main Execution Logic
# ============================================================
if uploaded_file:
    with st.expander("📄 Document Preview", expanded=False):
        uploaded_file.seek(0)
        show_pdf(uploaded_file.read())
        uploaded_file.seek(0)

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        start_btn = st.button("🚀 Initialize Analysis", type="primary", use_container_width=True)

    if start_btn:
        with st.spinner("Encrypting & Parsing Document..."):
            pdf_bytes = uploaded_file.read()
            pdf_text = extract_text_from_pdf(pdf_bytes)

        initial_state = {
            "pdf_text": pdf_text,
            "extracted_features": {},
            "features_to_check": [],
            "current_feature": None,
            "current_feature_value": None,
            "kb_results": "",
            "kb_sufficient": False,
            "web_results": "",
            "web_links": [],
            "findings": [],
            "report": "",
            "risk_level": "",
        }

        steps: List[Dict[str, Any]] = []
        history: List[Dict[str, str]] = []
        current_feature = None
        total_features = 0
        checked_count = 0

        modal = st.empty()
        modal_html = build_console_html(
            "Initializing Agents",
            "Preparing document for analysis…",
            0,
            len(STAGE_ORDER),
            history,
            "BOOT",
            agent_name="System Boot",
            links=[],
        )
        with modal:
            components.html(modal_html, height=540, scrolling=False)

        # Stream graph
        for step in compliance_graph.stream(initial_state, config={"recursion_limit": 300}):
            steps.append(step)
            node = list(step.keys())[0]

            title, desc = NODE_COPY.get(node, ("Processing", "Agents are working..."))
            idx = stage_index(node)
            badge = "LIVE"

            if node == "extract_features":
                ftc = step[node].get("features_to_check")
                if isinstance(ftc, list):
                    total_features = len(ftc)
                title = "Feature Extraction"
                desc = f"Identified {total_features} compliance vectors to analyze."
                history.append({"text": f"Found {total_features} rules in document", "tone": "ok"})

            if node == "select_next_feature":
                current_feature = step[node].get("current_feature")
                if current_feature:
                    checked_count += 1
                    nice = current_feature.replace("_", " ").upper()
                    denom = total_features if total_features else "?"
                    title = "Audit Protocol"
                    desc = f"Analyzing vector {checked_count}/{denom}: {nice}"
                    history.append({"text": f"Analyzing: {nice}", "tone": "ok"})
                else:
                    title = "Audit Finalization"
                    desc = "Synthesizing final compliance matrix."
                    history.append({"text": "All vectors analyzed", "tone": "ok"})

            if node == "search_kb" and current_feature:
                desc = f"Querying internal KB for {current_feature.replace('_',' ')}..."

            if node == "search_web" and current_feature:
                desc = f"Verifying official sources for {current_feature.replace('_',' ')}..."

            if node == "determine_compliance":
                findings = step[node].get("findings", [])
                if findings:
                    status = findings[0].get("status", "needs_review")
                    nice = (current_feature or "Rule").replace("_", " ")
                    if status == "compliant":
                        history.append({"text": f"{nice} -> PASSED", "tone": "ok"})
                    elif status == "gap":
                        history.append({"text": f"{nice} -> FAILED", "tone": "bad"})
                        badge = "ALERT"
                    else:
                        history.append({"text": f"{nice} -> REVIEW", "tone": "warn"})
                        badge = "WARN"

            if node == "generate_report":
                badge = "DONE"
                title = "Audit Complete"
                desc = "Report generated successfully."
                history.append({"text": "Report compiled", "tone": "ok"})

            agent_name = AGENT_FRIENDLY.get(node, "Agent")

            # IMPORTANT: show ONLY actual links returned by search_web
            links_for_modal: List[Dict[str, Any]] = []
            if node == "search_web":
                maybe_links = step[node].get("web_links", [])
                if isinstance(maybe_links, list):
                    links_for_modal = maybe_links

            modal_html = build_console_html(
                title,
                desc,
                idx,
                len(STAGE_ORDER),
                history,
                badge,
                agent_name=agent_name,
                links=links_for_modal,
            )
            with modal:
                components.html(modal_html, height=540, scrolling=False)

            if demo_mode and demo_delay > 0:
                time.sleep(demo_delay)

        if demo_mode:
            time.sleep(0.4)
        modal.empty()

        # ============================================================
        # Build outputs from steps
        # ============================================================
        final_state = steps[-1].get("generate_report", {}) if steps else {}

        # Pull findings
        all_findings: List[Dict[str, Any]] = []
        for s in steps:
            if "determine_compliance" in s:
                all_findings.extend(s["determine_compliance"].get("findings", []))

        # Pull extracted features for Summary tab
        extracted_features: Dict[str, Any] = {}
        for s in steps:
            if "extract_features" in s and isinstance(s["extract_features"], dict):
                extracted_features = s["extract_features"].get("extracted_features", {}) or {}
                break

        risk = final_state.get("risk_level", "Unknown")
        plan_name = uploaded_file.name

        report_pkg = compile_report(plan_name, risk, all_findings)
        md_report = report_to_markdown(report_pkg)
        pdf_out = markdown_to_simple_pdf_bytes("Compliance Audit Report", md_report)

        # ============================================================
        #  Results UI
        # ============================================================
        generated_at = report_pkg["meta"]["generated_at"]
        risk = report_pkg["meta"]["risk_level"]

        risk_chip_bg = {
            "Low": "rgba(34,197,94,0.15)",
            "Medium": "rgba(234,179,8,0.15)",
            "High": "rgba(239,68,68,0.15)",
        }.get(risk, "rgba(148,163,184,0.12)")
        risk_chip_fg = {"Low": "#22c55e", "Medium": "#eab308", "High": "#ef4444"}.get(risk, "#a3a3a3")

        hdr_l, hdr_r = st.columns([5, 1.35], vertical_alignment="center")
        with hdr_l:
            st.markdown(
                f"""
                <div class="report-header">
                  <div style="font-size:1.55rem; font-weight:900; color:#fff; line-height:1.1;">
                    {html.escape(plan_name.replace(".pdf",""))}
                  </div>
                  <div style="margin-top:8px; color:#9ca3af; font-size:0.92rem;">
                    Generated: {html.escape(generated_at)} &nbsp; • &nbsp; Risk Level:
                    <span class="chip" style="background:{risk_chip_bg}; color:{risk_chip_fg};">
                      {html.escape(risk.upper())}
                    </span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with hdr_r:
            st.download_button(
                "⬇️  Export Report",
                data=pdf_out,
                file_name="audit_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        tab_summary, tab_details, tab_sources = st.tabs(["Summary", "Details", "Sources"])

        # -------------------------
        # Summary
        # -------------------------
        with tab_summary:
            c = report_pkg["meta"]["counts"]
            left, right = st.columns([1, 1], gap="large")

            with left:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("#### COMPLIANCE BREAKDOWN")

                values = [c.get("compliant", 0), c.get("needs_review", 0), c.get("gap", 0)]
                labels = ["Compliant", "Review", "Gaps"]

                fig = go.Figure(
                    data=[go.Pie(labels=labels, values=values, hole=0.72, sort=False, textinfo="none")]
                )
                fig.update_layout(
                    margin=dict(l=0, r=0, t=0, b=0),
                    showlegend=True,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(font=dict(color="#e5e7eb")),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.markdown("</div>", unsafe_allow_html=True)

            with right:
                xf = extracted_features or {}
                elig = xf.get("eligibility", {}) or {}
                contrib = xf.get("contributions", {}) or {}
                vest = xf.get("vesting", {}) or {}
                auto = xf.get("auto_enrollment", {}) or {}

                plan_nm = xf.get("plan_name") or "—"
                eff_dt = xf.get("effective_date") or "—"
                eligibility = f"Age: {elig.get('age_requirement') or '—'}, Service: {elig.get('service_requirement') or '—'}"
                match = contrib.get("employer_match_formula") or "—"
                vesting = f"{vest.get('type') or '—'} — {vest.get('schedule') or '—'}"
                auto_enroll = f"{auto.get('enabled') if auto.get('enabled') is not None else '—'}, {auto.get('default_rate') or '—'}"

                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("#### EXTRACTED FEATURES")

                def row(label, value, last=False):
                    border = "" if last else "border-bottom:1px solid rgba(255,255,255,0.06);"
                    return f"""
                    <div style="display:flex; justify-content:space-between; gap:16px; padding:10px 0; {border}">
                      <span style="color:#9ca3af;">{html.escape(label)}</span>
                      <span style="color:#fff; font-weight:800; text-align:right;">{html.escape(str(value))}</span>
                    </div>
                    """

                st.markdown(
                    row("Plan Name", plan_nm)
                    + row("Effective Date", eff_dt)
                    + row("Eligibility", eligibility)
                    + row("Employer Match", match)
                    + row("Vesting", vesting)
                    + row("Auto-Enrollment", auto_enroll, last=True),
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

        # -------------------------
        # Details
        # -------------------------
        with tab_details:
            for f in all_findings:
                status = f.get("status", "needs_review")
                status_label = {"compliant": "COMPLIANT", "gap": "GAP", "needs_review": "REVIEW"}.get(status, "REVIEW")

                status_bg = {
                    "compliant": "rgba(34,197,94,0.12)",
                    "gap": "rgba(239,68,68,0.12)",
                    "needs_review": "rgba(234,179,8,0.12)",
                }.get(status, "rgba(234,179,8,0.12)")
                status_fg = {"compliant": "#22c55e", "gap": "#ef4444", "needs_review": "#eab308"}.get(
                    status, "#eab308"
                )

                feature_title = (f.get("feature") or "Unknown Feature").replace("_", " ").title()
                plan_value = f.get("plan_value", "—")
                regulation = f.get("regulation", "—")
                notes = (f.get("notes") or "").strip()

                icon = "✓" if status == "compliant" else ("×" if status == "gap" else "!")

                st.markdown(
                    f"""
                    <div style="
                      background: rgba(255,255,255,0.04);
                      border: 1px solid rgba(255,255,255,0.08);
                      border-radius: 16px;
                      padding: 18px;
                      margin-bottom: 14px;
                    ">
                      <div style="display:flex; justify-content:space-between; align-items:center; gap:14px;">
                        <div style="display:flex; align-items:center; gap:10px;">
                          <div style="width:28px; height:28px; border-radius:8px;
                                      background: rgba(255,255,255,0.06);
                                      display:flex; align-items:center; justify-content:center;
                                      color:#e5e7eb; font-weight:900;">
                            {icon}
                          </div>
                          <div style="color:#fff; font-weight:950; font-size:1.05rem;">
                            {html.escape(feature_title)}
                          </div>
                        </div>
                        <div style="
                          padding:6px 10px;
                          border-radius:999px;
                          background:{status_bg};
                          color:{status_fg};
                          font-weight:950;
                          font-size:0.8rem;
                          letter-spacing:0.04em;
                          border:1px solid rgba(255,255,255,0.06);
                        ">{html.escape(status_label)}</div>
                      </div>

                      <div style="display:flex; gap:18px; margin-top:12px; flex-wrap:wrap;">
                        <div style="min-width:220px;">
                          <div style="color:#9ca3af; font-size:0.85rem;">Plan Value</div>
                          <div style="color:#fff; font-weight:900; margin-top:2px;">{html.escape(str(plan_value))}</div>
                        </div>
                        <div style="min-width:260px;">
                          <div style="color:#9ca3af; font-size:0.85rem;">Regulation</div>
                          <div style="color:#fff; font-weight:900; margin-top:2px;">{html.escape(str(regulation))}</div>
                        </div>
                      </div>

                      <div style="
                        margin-top:14px;
                        background: rgba(0,0,0,0.20);
                        border: 1px solid rgba(255,255,255,0.06);
                        border-radius: 12px;
                        padding: 12px 14px;
                        color:#cbd5e1;
                        line-height:1.5;
                      ">
                        {html.escape(notes) if notes else "—"}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # -------------------------
        # Sources
        # -------------------------
        with tab_sources:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)

            sources = report_pkg.get("sources", []) or []
            if sources:
                for l in sources:
                    title = l.get("title") or "Official source"
                    url = l.get("url") or ""

                    st.markdown(
                        f"""
                        <div style="display:flex; justify-content:space-between; align-items:center;
                                    padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
                          <div>
                            <div style="font-weight:950; color:#a78bfa;">{html.escape(title)}</div>
                            <div style="color:#9ca3af; font-size:0.9rem;">{html.escape(url)}</div>
                          </div>
                          <div style="opacity:0.7;">↗</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if url:
                        st.link_button("Open", url)
            else:
                st.info("No external web sources were used for this audit.")

            st.markdown("</div>", unsafe_allow_html=True)

        # Optional: keep raw markdown available but not in the main UI
        with st.expander("Developer Output (Markdown)", expanded=False):
            st.code(md_report, language="markdown")

else:
    st.markdown(
        """
        <div style="text-align: center; padding: 60px 20px; color: #666;">
            <div style="font-size: 4rem; opacity: 0.2; margin-bottom: 20px;">📂</div>
            <h3>Awaiting Document</h3>
            <p>Upload a plan document to begin the AI compliance audit.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
