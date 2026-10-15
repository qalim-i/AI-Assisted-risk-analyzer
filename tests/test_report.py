from pathlib import Path

from report import build_markdown, generate_narratives, markdown_to_pdf
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


def test_narrative_generation_retries_invalid_json(monkeypatch) -> None:
    incident = IncidentExtraction.model_validate({
        "incident_type": "phishing", "affected_assets": [], "cve_ids": [], "iocs": [],
        "contained": True, "summary": "A phishing message was contained.",
    })
    risk = analyze_risk(incident, Path(__file__).parents[1] / "rules.yaml")
    responses = iter(["{not json}", '{"summary": "Contained phishing.", "recommendations": ["Review logs."]}'])
    monkeypatch.setattr("report.complete", lambda prompt, system: next(responses))
    assert generate_narratives(incident, risk) == ("Contained phishing.", ["Review logs."])
