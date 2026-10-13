"""Incident report narrative generation and Markdown/PDF rendering."""

from __future__ import annotations

import json
from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from xml.sax.saxutils import escape

from llm import complete
from risk import RiskAssessment
from schema import IncidentExtraction


def generate_narratives(incident: IncidentExtraction, risk: RiskAssessment) -> tuple[str, list[str]]:
    """Ask the LLM for only the report summary and recommended actions."""
    facts = json.dumps(incident.model_dump(mode="json"), indent=2)
    prompt = (
        "Using only these validated incident facts and risk result, return ONLY JSON with "
        "two keys: summary (a concise paragraph) and recommendations (an array of 3-6 "
        "specific, practical actions). Do not claim facts not in the supplied data.\n\n"
        f"Facts:\n{facts}\n\nRisk: {json.dumps(risk.as_dict())}"
    )
    try:
        result = json.loads(complete(prompt, "You write concise cybersecurity incident reports."))
        summary = result["summary"]
        recommendations = result["recommendations"]
        if not isinstance(summary, str) or not isinstance(recommendations, list) or not all(isinstance(item, str) for item in recommendations):
            raise ValueError("invalid narrative shape")
        return summary, recommendations
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError(f"The LLM returned invalid report narrative JSON: {error}") from error


def _value(value: Any) -> str:
    return "Not stated" if value is None or value == [] else str(value)


def build_markdown(
    incident: IncidentExtraction,
    risk: RiskAssessment,
    warnings: list[str],
    *,
    narrative_summary: str | None = None,
    recommendations: list[str] | None = None,
) -> str:
    """Build the canonical structured report in Markdown."""
    summary = narrative_summary or incident.summary
    actions = recommendations or ["Review the incident facts and follow the organization's incident-response process."]
    iocs = [f"- {ioc.type.value}: `{ioc.value}`" for ioc in incident.iocs] or ["- None identified"]
    assets = [f"- {asset}" for asset in incident.affected_assets] or ["- None stated"]
    cves = ", ".join(incident.cve_ids) or "None stated"
    quality = [f"- {warning}" for warning in warnings] or ["- No traceability warnings."]
    action_lines = [f"- {action}" for action in actions]
    return "\n".join([
        "# Cybersecurity Incident Report",
        "", "## Summary", summary,
        "", "## Incident Details",
        f"- Incident type: {incident.incident_type.value}",
        f"- Other type description: {_value(incident.other_type_description)}",
        f"- Detection source: {_value(incident.detection_source)}",
        f"- External source: {_value(incident.external_source)}",
        f"- Contained: {_value(incident.contained)}",
        f"- Data sensitivity: {_value(incident.data_sensitivity.value if incident.data_sensitivity else None)}",
        f"- Users affected: {_value(incident.users_affected)}",
        f"- Service disruption: {_value(incident.service_disruption_hours)} hours",
        f"- CVE IDs: {cves}",
        "", "## Affected Assets", *assets,
        "", "## Indicators of Compromise", *iocs,
        "", "## Risk Assessment",
        f"- Likelihood: {risk.likelihood}/5", f"- Impact: {risk.impact}/5",
        f"- Final score: {risk.score}/25 ({risk.band})",
        "", "### Likelihood Factors", *[f"- {factor}" for factor in risk.likelihood_factors],
        "", "### Impact Factors", *[f"- {factor}" for factor in risk.impact_factors],
        "", "## Recommended Actions", *action_lines,
        "", "## Data Quality Notes", *quality, "",
    ])


def markdown_to_pdf(markdown: str) -> bytes:
    """Convert report Markdown into a simple, portable PDF document."""
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    story = []
    for raw_line in markdown.splitlines():
        line = escape(raw_line)
        if raw_line.startswith("# "):
            story.append(Paragraph(line[2:], styles["Title"]))
        elif raw_line.startswith("## "):
            story.append(Spacer(1, 6))
            story.append(Paragraph(line[3:], styles["Heading2"]))
        elif raw_line.startswith("### "):
            story.append(Paragraph(line[4:], styles["Heading3"]))
        elif raw_line:
            story.append(Paragraph(line.replace("- ", "• ", 1), styles["BodyText"]))
        else:
            story.append(Spacer(1, 4))
    document.build(story)
    return output.getvalue()
