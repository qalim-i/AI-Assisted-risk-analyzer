from pathlib import Path

from report import build_markdown, markdown_to_pdf
from risk import analyze_risk
from schema import IncidentExtraction


def test_report_contains_required_sections() -> None:
    incident = IncidentExtraction.model_validate({
        "incident_type": "phishing", "affected_assets": ["email gateway"],
        "data_sensitivity": "internal", "cve_ids": [], "iocs": [],
        "contained": True, "summary": "A phishing message was contained.",
    })
    risk = analyze_risk(incident, Path(__file__).parents[1] / "rules.yaml")
    markdown = build_markdown(incident, risk, ["Example warning"])
    for section in ("Summary", "Incident Details", "Affected Assets", "Indicators of Compromise", "Risk Assessment", "Recommended Actions", "Data Quality Notes"):
        assert f"## {section}" in markdown
    assert markdown_to_pdf(markdown).startswith(b"%PDF")
