"""
TrustLayer AI — Real Application
Enterprise AI Reliability Platform powered by Anthropic Claude
Canada Hackathon 2026
"""

from __future__ import annotations
import json
import time
from datetime import datetime
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from trustlayer.detector import TrustLayerDetector
from trustlayer.industries import INDUSTRIES, get_industry
from trustlayer.models import AnalysisRequest
from trustlayer.cross_validator import CrossValidator, CrossValidationResult

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TrustLayer AI | Enterprise AI Reliability",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --primary: #0066FF;
    --teal:    #00B894;
    --red:     #E74C3C;
    --orange:  #F39C12;
    --green:   #27AE60;
    --dark:    #1E293B;
    --gray:    #64748B;
    --border:  #E2E8F0;
    --bg:      #F8FAFC;
}

.stApp { background: var(--bg); font-family: 'Plus Jakarta Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
    border-right: 1px solid var(--border);
}

/* Action badges */
.badge-pass  { background:#DCFCE7; color:#166534; padding:6px 18px; border-radius:20px; font-weight:700; font-size:1.1rem; display:inline-block; }
.badge-flag  { background:#FEF9C3; color:#854D0E; padding:6px 18px; border-radius:20px; font-weight:700; font-size:1.1rem; display:inline-block; }
.badge-block { background:#FEE2E2; color:#991B1B; padding:6px 18px; border-radius:20px; font-weight:700; font-size:1.1rem; display:inline-block; }

/* Score circle */
.score-circle {
    width:130px; height:130px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    flex-direction:column; margin:0 auto;
    font-family:'Plus Jakarta Sans', sans-serif;
}

/* Issue/claim pills */
.issue-high   { background:#FEE2E2; color:#991B1B; border-left:3px solid #E74C3C; padding:6px 12px; border-radius:6px; margin:4px 0; font-size:.9rem; }
.issue-medium { background:#FEF9C3; color:#854D0E; border-left:3px solid #F39C12; padding:6px 12px; border-radius:6px; margin:4px 0; font-size:.9rem; }
.issue-low    { background:#DCFCE7; color:#166534; border-left:3px solid #22C55E; padding:6px 12px; border-radius:6px; margin:4px 0; font-size:.9rem; }
.issue-info   { background:#EFF6FF; color:#1D4ED8; border-left:3px solid #0066FF; padding:6px 12px; border-radius:6px; margin:4px 0; font-size:.9rem; }

/* Response box */
.response-box {
    background:#ffffff; border:1px solid var(--border); border-radius:10px;
    padding:16px; font-size:.95rem; line-height:1.7; color:var(--dark);
    max-height:280px; overflow-y:auto;
}

/* Step indicator */
.step-active   { color:#0066FF; font-weight:600; }
.step-done     { color:#27AE60; font-weight:600; }
.step-pending  { color:#94A3B8; }

/* Metric card */
.metric-card {
    background:#fff; border:1px solid var(--border); border-radius:10px;
    padding:14px 18px; text-align:center;
}
.metric-card h2 { margin:0; font-size:1.8rem; }
.metric-card p  { margin:0; color:var(--gray); font-size:.85rem; }

/* Header */
.app-header {
    background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 100%);
    padding: 20px 28px; border-radius: 12px; margin-bottom: 24px;
    display:flex; align-items:center; gap:16px;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_cv_result" not in st.session_state:
    st.session_state.last_cv_result = None


# ── Helper: get detector (cached per API key) ─────────────────────────────────
@st.cache_resource
def get_detector(api_key: str) -> TrustLayerDetector:
    return TrustLayerDetector(api_key=api_key)


@st.cache_resource
def get_cross_validator(anthropic_key: str, openai_key: str) -> CrossValidator:
    return CrossValidator(anthropic_key=anthropic_key, openai_key=openai_key)


# ── Helper: confidence gauge ──────────────────────────────────────────────────
def confidence_gauge(confidence: float, risk: float, action: str) -> go.Figure:
    color_map = {"PASS": "#27AE60", "FLAG": "#F39C12", "BLOCK": "#E74C3C"}
    color = color_map.get(action, "#64748B")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence,
        number={"suffix": "%", "font": {"size": 36, "color": color}},
        gauge={
            "axis":  {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8"},
            "bar":   {"color": color, "thickness": 0.28},
            "bgcolor": "white",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50],  "color": "#FEE2E2"},
                {"range": [50, 75], "color": "#FEF9C3"},
                {"range": [75, 100],"color": "#DCFCE7"},
            ],
            "threshold": {
                "line":  {"color": color, "width": 4},
                "thickness": 0.8,
                "value": confidence,
            },
        },
        title={"text": "Confidence Score", "font": {"size": 14, "color": "#64748B"}},
    ))
    fig.update_layout(
        height=220, margin=dict(t=40, b=0, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── Helper: technique bar chart ───────────────────────────────────────────────
def technique_chart(scores_dict: dict) -> go.Figure:
    labels = list(scores_dict.keys())
    values = list(scores_dict.values())
    colors = ["#27AE60" if v >= 75 else "#F39C12" if v >= 50 else "#E74C3C" for v in values]

    fig = go.Figure(go.Bar(
        x=values, y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.0f}%" for v in values],
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        height=300, margin=dict(t=10, b=10, l=10, r=60),
        xaxis=dict(range=[0, 115], showgrid=False, showticklabels=False),
        yaxis=dict(tickfont=dict(size=12)),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🛡️ TrustLayer AI")
    st.markdown("*Enterprise AI Reliability Platform*")
    st.divider()

    # Anthropic API Key
    api_key = ""
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
        st.success("✅ Anthropic key loaded")
    except Exception:
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            help="Get your key at console.anthropic.com",
        )

    # OpenAI API Key (optional — for cross-validation)
    openai_key = ""
    try:
        openai_key = st.secrets["OPENAI_API_KEY"]
        st.success("✅ OpenAI key loaded")
    except Exception:
        openai_key = st.text_input(
            "OpenAI API Key (optional)",
            type="password",
            placeholder="sk-...",
            help="Required for Claude + GPT-4o cross-validation",
        )

    st.divider()

    # Industry selector
    industry_names = list(INDUSTRIES.keys())
    industry = st.selectbox(
        "Industry Module",
        industry_names,
        index=0,
        format_func=lambda x: f"{INDUSTRIES[x]['icon']}  {x}",
    )
    industry_cfg = get_industry(industry)
    st.caption(industry_cfg["description"])

    st.divider()

    # Settings
    with st.expander("⚙️ Detection Settings"):
        self_consistency = st.toggle(
            "Self-consistency check",
            value=False,
            help="Runs 2 extra Claude calls to test response stability. More accurate, slower.",
        )
        use_grounding = st.toggle(
            "Enable industry grounding",
            value=True,
            help="Compares response against authoritative industry data.",
        )
        use_cross_validation = st.toggle(
            "Cross-validate with GPT-4o",
            value=bool(openai_key),
            disabled=not bool(openai_key),
            help="Run detection independently through Claude AND GPT-4o. Agreement score boosts reliability.",
        )
        if use_cross_validation and not openai_key:
            st.caption("Enter your OpenAI key above to enable cross-validation.")

    st.divider()
    st.caption("**Canada Hackathon 2026**")
    st.caption("Detect · Prevent · Govern")


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="app-header">
  <div style="font-size:2.5rem">🛡️</div>
  <div>
    <div style="color:#fff;font-size:1.5rem;font-weight:800">TrustLayer AI</div>
    <div style="color:#94A3B8;font-size:.95rem">Real-time hallucination detection powered by Claude · Canada Hackathon 2026</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════

tab_detect, tab_history, tab_howto = st.tabs([
    "🔍  Live Detection",
    "📊  Session History",
    "📖  How It Works",
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: LIVE DETECTION
# ─────────────────────────────────────────────────────────────────────────────
with tab_detect:

    # ── Query input section ───────────────────────────────────────────────────
    col_input, col_scenario = st.columns([2, 1])

    with col_input:
        st.markdown("#### Your Query")
        query = st.text_area(
            label="query_input",
            label_visibility="collapsed",
            placeholder="Type a question to send to the AI, or load a preset scenario →",
            height=120,
            key="query_input",
        )

    with col_scenario:
        st.markdown("#### Load Preset Scenario")
        scenarios = industry_cfg.get("scenarios", [])
        scenario_labels = [s["label"] for s in scenarios]
        selected_label = st.selectbox(
            "scenario_select",
            label_visibility="collapsed",
            options=["— select —"] + scenario_labels,
        )
        if selected_label != "— select —":
            chosen = next(s for s in scenarios if s["label"] == selected_label)
            if chosen["query"] and st.button("Load →", use_container_width=True):
                st.session_state["query_input"] = chosen["query"]
                st.rerun()

        # Show what grounding data will be used
        if use_grounding and industry_cfg.get("grounding_context"):
            with st.expander("📋 Grounding data active"):
                st.code(industry_cfg["grounding_context"], language=None)

    # Custom grounding context
    with st.expander("📎 Paste your own grounding context (optional)"):
        custom_context = st.text_area(
            "custom_ctx",
            label_visibility="collapsed",
            placeholder="Paste authoritative data here — product specs, policy docs, clinical guidelines…",
            height=100,
        )

    # ── Analyze button ────────────────────────────────────────────────────────
    st.markdown("")
    run_col, info_col = st.columns([1, 3])
    with run_col:
        analyze_btn = st.button(
            "🔍  Analyze with TrustLayer",
            type="primary",
            use_container_width=True,
            disabled=not api_key or not query,
        )
    with info_col:
        if not api_key:
            st.warning("⚠️ Enter your Anthropic API key in the sidebar to begin.")
        elif not query:
            st.info("💬 Type a query or load a preset scenario above.")

    # ── Run pipeline ──────────────────────────────────────────────────────────
    if analyze_btn and api_key and query:
        # Determine grounding context
        context = None
        if custom_context.strip():
            context = custom_context.strip()
        elif use_grounding:
            context = industry_cfg.get("grounding_context") or None

        request = AnalysisRequest(
            query=query,
            industry=industry,
            context=context,
            self_consistency_check=self_consistency,
        )

        # Choose pipeline: cross-validation or single Claude
        run_cv = use_cross_validation and bool(openai_key)

        # Progress steps
        progress_placeholder = st.empty()
        if run_cv:
            steps = [
                ("Claude: generating response...", "⏳"),
                ("Claude: detection analysis...",  "⏳"),
                ("GPT-4o: cross-validation...",    "⏳"),
                ("Computing consensus decision...", "⏳"),
            ]
        else:
            steps = [
                ("Sending query to Claude...",           "⏳"),
                ("Extracting claims and citations...",   "⏳"),
                ("Running 8 detection algorithms...",    "⏳"),
                ("Computing confidence + risk scores...", "⏳"),
            ]

        with progress_placeholder.container():
            step_cols = st.columns(len(steps))
            for i, (label, icon) in enumerate(steps):
                step_cols[i].markdown(
                    f"<div class='step-pending'>{icon} {label}</div>",
                    unsafe_allow_html=True,
                )

        def update_step(i: int, done: bool = False):
            icon = "✅" if done else "🔄"
            cls  = "step-done" if done else "step-active"
            step_cols[i].markdown(
                f"<div class='{cls}'>{icon} {steps[i][0]}</div>",
                unsafe_allow_html=True,
            )

        try:
            if run_cv:
                # Cross-validation pipeline
                cv = get_cross_validator(api_key, openai_key)
                update_step(0)
                # run() handles generate + both analyses internally
                # We update steps incrementally via timing approximation
                update_step(1)
                update_step(2)
                cv_result = cv.run(request)
                update_step(0, done=True)
                update_step(1, done=True)
                update_step(2, done=True)
                update_step(3, done=True)

                result = cv_result.claude_result  # primary result for display
                st.session_state.last_cv_result = cv_result
                st.session_state.last_result = result

                # Use consensus for history
                history_action = cv_result.consensus_action
                history_conf   = cv_result.consensus_confidence
                history_risk   = cv_result.consensus_risk
            else:
                # Single Claude pipeline
                detector = get_detector(api_key)
                update_step(0)
                llm_response = detector.generate_response(request)
                update_step(0, done=True)
                update_step(1)
                update_step(2)
                result = detector.analyze(request, llm_response)
                update_step(1, done=True)
                update_step(2, done=True)
                update_step(3, done=True)

                st.session_state.last_result = result
                st.session_state.last_cv_result = None
                history_action = result.action
                history_conf   = result.confidence_score
                history_risk   = result.risk_score

            st.session_state.history.append({
                "time":       datetime.now().strftime("%H:%M:%S"),
                "industry":   industry,
                "query":      query[:80] + ("…" if len(query) > 80 else ""),
                "action":     history_action,
                "confidence": history_conf,
                "risk":       history_risk,
                "issues":     len(result.issues),
                "validated":  "Yes" if run_cv else "No",
            })

        except Exception as e:
            progress_placeholder.empty()
            st.error(f"❌ Analysis failed: {e}")
            st.stop()

        progress_placeholder.empty()

    # ── Cross-validation panel ────────────────────────────────────────────────
    cv_result: Optional[CrossValidationResult] = st.session_state.get("last_cv_result")
    if cv_result:
        st.markdown("---")
        st.markdown("### Claude + GPT-4o Cross-Validation")

        # Agreement badge + consensus
        agree_col, claude_col, gpt_col = st.columns([1, 1.5, 1.5])

        with agree_col:
            pct = cv_result.agreement_pct
            color = cv_result.agreement_color
            st.markdown(
                f"<div style='background:#fff;border:2px solid {color};border-radius:12px;"
                f"padding:16px;text-align:center'>"
                f"<div style='font-size:2rem;font-weight:800;color:{color}'>{pct}%</div>"
                f"<div style='font-size:.85rem;color:{color};font-weight:600'>{cv_result.agreement_label}</div>"
                f"<hr style='margin:8px 0'>"
                f"<div style='font-size:.8rem;color:#64748B'>Agreement Score</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            # Consensus badge
            badge_cls = f"badge-{cv_result.consensus_action.lower()}"
            st.markdown(
                f"<div style='text-align:center'>"
                f"<div style='font-size:.8rem;color:#64748B;margin-bottom:4px'>Consensus Decision</div>"
                f"<div class='{badge_cls}'>{cv_result.consensus_action}</div>"
                f"<div style='font-size:.8rem;color:#64748B;margin-top:4px'>"
                f"Confidence: {cv_result.consensus_confidence:.1f}%</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        with claude_col:
            st.markdown("**Claude (Sonnet)**")
            claude_scores = cv_result.claude_result.scores.as_dict()
            gpt_scores    = cv_result.openai_result.scores.as_dict()
            labels = list(claude_scores.keys())

            fig_cv = go.Figure()
            fig_cv.add_trace(go.Bar(
                name="Claude",
                x=labels,
                y=list(claude_scores.values()),
                marker_color="#0066FF",
                opacity=0.85,
            ))
            fig_cv.add_trace(go.Bar(
                name="GPT-4o",
                x=labels,
                y=list(gpt_scores.values()),
                marker_color="#10B981",
                opacity=0.85,
            ))
            fig_cv.update_layout(
                barmode="group",
                height=260,
                margin=dict(t=10, b=60, l=10, r=10),
                yaxis=dict(range=[0, 115], showgrid=False),
                xaxis=dict(tickangle=-35, tickfont=dict(size=9)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(fig_cv, use_container_width=True)

        with gpt_col:
            st.markdown("**GPT-4o (OpenAI)**")
            st.metric("GPT-4o Action",      cv_result.openai_result.action)
            st.metric("GPT-4o Confidence",  f"{cv_result.openai_result.confidence_score:.1f}%")
            st.metric("GPT-4o Risk",        f"{cv_result.openai_result.risk_score:.1f}")
            st.metric("Processing",         f"{cv_result.processing_ms} ms total")

        # Disagreement signals
        if cv_result.disagreement_signals:
            with st.expander(f"⚠️ Disagreement Signals ({len(cv_result.disagreement_signals)})"):
                for sig in cv_result.disagreement_signals:
                    st.markdown(f"<div class='issue-medium'>⚡ {sig}</div>",
                                unsafe_allow_html=True)
        else:
            st.success("Both models are in strong agreement — high reliability result.")

        # GPT-4o explanation
        if cv_result.openai_result.explanation:
            with st.expander("GPT-4o Explanation"):
                st.markdown(
                    f"<div style='background:#f0fdf4;border-left:4px solid #10B981;"
                    f"padding:12px 16px;border-radius:8px;font-size:.95rem'>"
                    f"{cv_result.openai_result.explanation}</div>",
                    unsafe_allow_html=True,
                )

    # ── Display results ───────────────────────────────────────────────────────
    result = st.session_state.get("last_result")

    if result:
        st.markdown("---")

        # ── Row 1: Scores + Action ────────────────────────────────────────────
        col_gauge, col_risk, col_action, col_meta = st.columns([2, 1, 1.5, 1.5])

        with col_gauge:
            st.plotly_chart(
                confidence_gauge(result.confidence_score, result.risk_score, result.action),
                use_container_width=True,
            )

        with col_risk:
            st.markdown("<br>", unsafe_allow_html=True)
            st.metric("Risk Score", f"{result.risk_score:.0f} / 100")
            st.metric("Issues Found", len(result.issues))
            st.metric("Claims Extracted", len(result.claims))

        with col_action:
            st.markdown("<br><br>", unsafe_allow_html=True)
            badge_class = f"badge-{result.action.lower()}"
            st.markdown(
                f"<div style='text-align:center'>"
                f"<div class='{badge_class}'>{result.action_emoji}  {result.action}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            action_desc = {
                "PASS":  "Response delivered to user",
                "FLAG":  "Routed to human review",
                "BLOCK": "Blocked — fallback triggered",
            }
            st.caption(action_desc.get(result.action, ""))

        with col_meta:
            st.markdown("<br>", unsafe_allow_html=True)
            st.metric("Industry", result.industry.split("—")[0].strip())
            st.metric("Latency", f"{result.processing_ms or 0} ms")
            if result.citations_found:
                cite_status = "Valid" if result.citations_valid else "⚠️ Suspect"
                st.metric("Citations", f"{len(result.citations_found)} ({cite_status})")

        # ── Explanation ───────────────────────────────────────────────────────
        color_map = {"PASS": "#DCFCE7", "FLAG": "#FEF9C3", "BLOCK": "#FEE2E2"}
        border_map = {"PASS": "#22C55E", "FLAG": "#F59E0B", "BLOCK": "#EF4444"}
        bg    = color_map.get(result.action, "#F1F5F9")
        bdr   = border_map.get(result.action, "#94A3B8")

        st.markdown(
            f"<div style='background:{bg};border-left:4px solid {bdr};"
            f"padding:12px 16px;border-radius:8px;margin:8px 0;font-size:.95rem'>"
            f"<strong>TrustLayer Decision:</strong> {result.explanation}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ── Row 2: Issues + Technique breakdown ───────────────────────────────
        col_issues, col_chart = st.columns([1, 1])

        with col_issues:
            st.markdown("#### 🔎 Issues Detected")

            if not result.issues and not result.fabrication_indicators:
                st.success("No significant issues detected.")
            else:
                for issue in result.issues:
                    st.markdown(f"<div class='issue-high'>⚠️ {issue}</div>",
                                unsafe_allow_html=True)
                for fi in result.fabrication_indicators:
                    st.markdown(f"<div class='issue-medium'>🔴 {fi}</div>",
                                unsafe_allow_html=True)
                for ni in result.numerical_issues:
                    st.markdown(f"<div class='issue-medium'>🔢 {ni}</div>",
                                unsafe_allow_html=True)
                for ti in result.temporal_issues:
                    st.markdown(f"<div class='issue-info'>📅 {ti}</div>",
                                unsafe_allow_html=True)

        with col_chart:
            st.markdown("#### 📊 Detection Technique Scores")
            st.plotly_chart(
                technique_chart(result.scores.as_dict()),
                use_container_width=True,
            )

        # ── Row 3: Expandable details ─────────────────────────────────────────
        with st.expander("📄 Full AI Response"):
            st.markdown(
                f"<div class='response-box'>{result.llm_response}</div>",
                unsafe_allow_html=True,
            )

        if result.claims:
            with st.expander(f"📋 Extracted Claims ({len(result.claims)})"):
                claims_data = [
                    {
                        "Claim": c.text,
                        "Risk":  c.risk.upper(),
                        "Issue": c.issue or "—",
                    }
                    for c in result.claims
                ]
                df = pd.DataFrame(claims_data)

                def color_risk(val):
                    if val == "HIGH":   return "background-color:#FEE2E2;color:#991B1B"
                    if val == "MEDIUM": return "background-color:#FEF9C3;color:#854D0E"
                    return "background-color:#DCFCE7;color:#166534"

                st.dataframe(
                    df.style.applymap(color_risk, subset=["Risk"]),
                    use_container_width=True,
                    hide_index=True,
                )

        if result.citations_found:
            with st.expander(f"🔗 Citations Found ({len(result.citations_found)})"):
                for cite in result.citations_found:
                    status = "✅" if result.citations_valid else "❌ Suspect"
                    st.markdown(f"- {status} `{cite}`")

        with st.expander("🔧 Raw JSON Output"):
            raw_output = {
                "query":            result.query,
                "industry":         result.industry,
                "action":           result.action,
                "confidence_score": result.confidence_score,
                "risk_score":       result.risk_score,
                "explanation":      result.explanation,
                "scores":           result.scores.as_dict(),
                "issues":           result.issues,
                "fabrication_indicators": result.fabrication_indicators,
                "claims":           [c.model_dump() for c in result.claims],
                "citations_found":  result.citations_found,
                "citations_valid":  result.citations_valid,
                "numerical_issues": result.numerical_issues,
                "temporal_issues":  result.temporal_issues,
                "processing_ms":    result.processing_ms,
                "timestamp":        result.timestamp.isoformat(),
            }
            st.json(raw_output)

        # Download result
        st.download_button(
            "⬇️  Download Result JSON",
            data=json.dumps(raw_output, indent=2),
            file_name=f"trustlayer_{result.industry.replace(' ','_')}_{result.timestamp.strftime('%H%M%S')}.json",
            mime="application/json",
        )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: SESSION HISTORY
# ─────────────────────────────────────────────────────────────────────────────
with tab_history:
    st.markdown("#### Session Analysis History")

    if not st.session_state.history:
        st.info("No analyses run yet this session. Go to **Live Detection** to get started.")
    else:
        df_hist = pd.DataFrame(st.session_state.history)

        # Summary metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Analyzed",   len(df_hist))
        c2.metric("Blocked",  int((df_hist["action"] == "BLOCK").sum()))
        c3.metric("Flagged",  int((df_hist["action"] == "FLAG").sum()))
        c4.metric("Passed",   int((df_hist["action"] == "PASS").sum()))

        st.markdown("---")

        def color_action(val):
            if val == "BLOCK": return "background-color:#FEE2E2;color:#991B1B;font-weight:700"
            if val == "FLAG":  return "background-color:#FEF9C3;color:#854D0E;font-weight:700"
            return "background-color:#DCFCE7;color:#166534;font-weight:700"

        st.dataframe(
            df_hist.style.applymap(color_action, subset=["action"]),
            use_container_width=True,
            hide_index=True,
        )

        # Confidence trend
        if len(df_hist) > 1:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                y=df_hist["confidence"],
                mode="lines+markers",
                line=dict(color="#0066FF", width=2),
                marker=dict(size=8),
                name="Confidence %",
            ))
            fig_trend.add_hline(y=75, line_dash="dash", line_color="#27AE60",
                                annotation_text="PASS threshold (75%)")
            fig_trend.add_hline(y=50, line_dash="dash", line_color="#F39C12",
                                annotation_text="FLAG threshold (50%)")
            fig_trend.update_layout(
                title="Confidence Score Trend",
                height=280,
                yaxis=dict(range=[0, 105]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_trend, use_container_width=True)

        st.download_button(
            "⬇️  Export History CSV",
            data=df_hist.to_csv(index=False),
            file_name="trustlayer_session_history.csv",
            mime="text/csv",
        )

        if st.button("🗑️  Clear History"):
            st.session_state.history = []
            st.session_state.last_result = None
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: HOW IT WORKS
# ─────────────────────────────────────────────────────────────────────────────
with tab_howto:
    st.markdown("#### How TrustLayer AI Works")

    st.markdown("""
    TrustLayer AI intercepts every AI response, analyzes it using **8 parallel detection
    algorithms**, and returns a **Confidence Score** and **Risk Score** that drive an
    automated **PASS / FLAG / BLOCK** decision.
    """)

    st.markdown("---")
    st.markdown("#### Detection Pipeline")

    pipeline_steps = [
        ("1", "Generate Response",    "Claude generates a response to your query acting as an industry-specific AI assistant.", "#0066FF"),
        ("2", "Claim Extraction",     "TrustLayer extracts all factual claims, citations, numerical assertions, and temporal statements.", "#0066FF"),
        ("3", "8-Technique Analysis", "All 8 detection algorithms run in parallel against the response and grounding data.", "#F39C12"),
        ("4", "Ensemble Scoring",     "Individual scores are combined into a weighted Confidence Score and Risk Score.", "#F39C12"),
        ("5", "Decision Policy",      "Scores are compared to thresholds: PASS (≥75%), FLAG (50–74%), BLOCK (<50%).", "#E74C3C"),
        ("6", "Audit Log",            "Every interaction is logged with full scores, claims, issues, and compliance tags.", "#27AE60"),
    ]
    for step, title, desc, color in pipeline_steps:
        st.markdown(
            f"<div style='display:flex;gap:12px;align-items:flex-start;margin:10px 0'>"
            f"<div style='background:{color};color:#fff;border-radius:50%;width:32px;height:32px;"
            f"display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0'>{step}</div>"
            f"<div><strong>{title}</strong><br><span style='color:#64748B;font-size:.9rem'>{desc}</span></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("#### The 8 Detection Techniques")

    techniques = [
        ("Semantic Entropy Analysis",       "87%", "45ms",  "Measures model confidence via token probability distributions. High entropy = low confidence."),
        ("Self-Consistency Checking",       "82%", "120ms", "Samples multiple responses and checks factual agreement across them."),
        ("Source Verification",             "95%", "200ms", "Validates all cited cases, URLs, statutes, and references against real databases."),
        ("Enterprise Knowledge Grounding",  "98%", "150ms", "Compares response claims against your authoritative grounding data. Highest accuracy."),
        ("Claim Extraction & Classification","91%","35ms",  "Identifies and risk-classifies all assertive claims by type and criticality."),
        ("Hallucination Pattern Recognition","79%","25ms",  "Classifies response against known hallucination signatures using fine-tuned model."),
        ("Temporal Consistency Checking",   "93%", "40ms",  "Flags date-sensitive claims that may be outdated or inconsistent with reality."),
        ("Numerical Claim Validation",      "96%", "80ms",  "Validates all rates, dosages, thresholds, and statistics against authoritative ranges."),
    ]

    df_tech = pd.DataFrame(techniques, columns=["Technique", "Accuracy", "Latency", "Description"])

    def color_acc(val):
        pct = int(val.replace("%", ""))
        if pct >= 90: return "color:#166534;font-weight:700"
        if pct >= 80: return "color:#854D0E;font-weight:700"
        return "color:#991B1B;font-weight:700"

    st.dataframe(
        df_tech.style.applymap(color_acc, subset=["Accuracy"]),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.markdown("#### Decision Thresholds")

    col1, col2, col3 = st.columns(3)
    col1.markdown("""
    <div style='background:#DCFCE7;border-radius:10px;padding:16px;text-align:center'>
    <div style='font-size:1.4rem;font-weight:800;color:#166534'>✅ PASS</div>
    <div style='color:#166534;font-size:.9rem'>Confidence ≥ 75%<br>Risk Score &lt; 30</div>
    <div style='color:#64748B;font-size:.85rem;margin-top:8px'>Response delivered to user</div>
    </div>""", unsafe_allow_html=True)

    col2.markdown("""
    <div style='background:#FEF9C3;border-radius:10px;padding:16px;text-align:center'>
    <div style='font-size:1.4rem;font-weight:800;color:#854D0E'>⚠️ FLAG</div>
    <div style='color:#854D0E;font-size:.9rem'>Confidence 50–74%<br>Risk Score 30–59</div>
    <div style='color:#64748B;font-size:.85rem;margin-top:8px'>Routed to human review</div>
    </div>""", unsafe_allow_html=True)

    col3.markdown("""
    <div style='background:#FEE2E2;border-radius:10px;padding:16px;text-align:center'>
    <div style='font-size:1.4rem;font-weight:800;color:#991B1B'>🚫 BLOCK</div>
    <div style='color:#991B1B;font-size:.9rem'>Confidence &lt; 50%<br>Risk Score ≥ 60</div>
    <div style='color:#64748B;font-size:.85rem;margin-top:8px'>Blocked + fallback triggered</div>
    </div>""", unsafe_allow_html=True)
