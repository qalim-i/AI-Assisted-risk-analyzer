"""Streamlit interface for the AI-Assisted Incident Report and Risk Analyzer."""

from __future__ import annotations

import csv
import json
import os
from io import StringIO
from pathlib import Path

import streamlit as st

from extractor import ExtractionError, extract_incident
from report import build_markdown, generate_narratives, markdown_to_pdf
from risk import analyze_risk
from validator import validate_data_quality


ROOT = Path(__file__).parent
SAMPLES = ROOT / "data" / "samples"


def _render_risk_chart(risk: dict[str, object]) -> None:
    """Render a compact visual comparison of the two component scores."""
    likelihood = int(risk["likelihood"])
    impact = int(risk["impact"])
    chart_data = {
        "Risk component": ["Likelihood", "Impact"],
        "Score": [likelihood, impact],
    }
    st.bar_chart(chart_data, x="Risk component", y="Score", horizontal=True)
    st.caption("Each bar is measured on the same 1–5 scale.")

    first, second = st.columns(2)
    with first:
        st.caption(f"Likelihood · {likelihood}/5")
        st.progress(likelihood / 5)
    with second:
        st.caption(f"Impact · {impact}/5")
        st.progress(impact / 5)


def _read_upload(uploaded: object | None) -> str:
    """Decode a Streamlit text upload as UTF-8."""
    if uploaded is None:
        return ""
    return uploaded.getvalue().decode("utf-8")  # type: ignore[union-attr]


def _count_alerts(uploaded: object | None) -> int:
    """Count data rows in an optional CSV alert file."""
    content = _read_upload(uploaded)
    if not content.strip():
        return 0
    return sum(1 for _ in csv.DictReader(StringIO(content)))


def main() -> None:
    """Render the one-page analyzer."""
    st.set_page_config(page_title="Incident Risk Analyzer", layout="wide")
    st.title("AI-Assisted Cybersecurity Incident Report and Risk Analyzer")
    #st.warning("Advisory only: this rule-based risk rating supports human review; it is not a substitute for incident-response decisions.")

    left, right = st.columns([1, 1.35], gap="large")
    with left:
        names = ["Custom input", *[path.name for path in sorted(SAMPLES.glob("*.txt"))]]
        choice = st.selectbox("Demo sample", names)
        sample_text = "" if choice == "Custom input" else (SAMPLES / choice).read_text(encoding="utf-8")
        uploaded_text = st.file_uploader("Or upload an incident (.txt)", type=["txt"])
        description = st.text_area("Incident description", value=_read_upload(uploaded_text) or sample_text, height=320)
        alerts = st.file_uploader("Optional alerts (.csv)", type=["csv"])
        st.caption("CSV rows are counted as corroborating alerts; more than one adds the configured repeated-events likelihood factor.")
        if not os.getenv("LLM_PROVIDER") or not os.getenv("LLM_MODEL"):
            st.info("LLM setup is required before analysis. Set LLM_PROVIDER and LLM_MODEL in the terminal, then restart Streamlit. See README.md for OpenAI and Ollama examples.")
        run = st.button("Analyze incident", type="primary", use_container_width=True)

    if run:
        try:
            with st.spinner("Extracting facts and composing the report…"):
                incident = extract_incident(description)
                warnings = validate_data_quality(incident, description)
                alert_count = _count_alerts(alerts)
                assessment = analyze_risk(incident, ROOT / "rules.yaml", alert_count=alert_count)
                narrative_summary, recommendations = generate_narratives(incident, assessment)
                markdown = build_markdown(incident, assessment, warnings, narrative_summary=narrative_summary, recommendations=recommendations)
                result_json = {"incident": incident.model_dump(mode="json"), "risk": assessment.as_dict(), "warnings": warnings}
                st.session_state.analysis = {"markdown": markdown, "pdf": markdown_to_pdf(markdown), "json": result_json, "risk": assessment.as_dict(), "warnings": warnings}
        except (ExtractionError, RuntimeError, ValueError, UnicodeDecodeError, csv.Error) as error:
            st.error(f"Analysis could not be completed: {error}")

    with right:
        result = st.session_state.get("analysis")
        if not result:
            st.info("Select a sample or enter an incident description, then choose Analyze incident.")
            return
        tabs = st.tabs(["Report", "Risk Breakdown", "Extracted JSON", "Warnings"])
        with tabs[0]:
            st.markdown(result["markdown"])
            st.download_button("Download Markdown", result["markdown"], "incident-report.md", "text/markdown")
            st.download_button("Download PDF", result["pdf"], "incident-report.pdf", "application/pdf")
        with tabs[1]:
            risk = result["risk"]
            st.metric("Risk score", f"{risk['score']}/10", risk["band"])
            first, second = st.columns(2)
            first.metric("Likelihood", f"{risk['likelihood']}/5")
            second.metric("Impact", f"{risk['impact']}/5")
            st.subheader("Risk score visual")
            _render_risk_chart(risk)
            st.subheader("Likelihood factors")
            st.write(risk["likelihood_factors"])
            st.subheader("Impact factors")
            st.write(risk["impact_factors"])
        with tabs[2]:
            rendered = json.dumps(result["json"], indent=2)
            st.code(rendered, language="json")
            st.download_button("Download JSON", rendered, "incident-analysis.json", "application/json")
        with tabs[3]:
            if result["warnings"]:
                for warning in result["warnings"]:
                    st.warning(warning)
            else:
                st.success("No traceability or completeness warnings.")


if __name__ == "__main__":
    main()
