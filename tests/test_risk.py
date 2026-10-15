from pathlib import Path

from schema import IncidentExtraction
from risk import analyze_risk, risk_band

RULES = Path(__file__).parents[1] / "rules.yaml"


def test_risk_band_mapping() -> None:
    bands = {"low_max": 3, "medium_max": 5, "high_max": 8}
    assert [risk_band(score, bands) for score in (2, 3, 4, 5, 6, 8, 9, 10)] == ["Low", "Low", "Medium", "Medium", "High", "High", "Critical", "Critical"]


def test_risk_engine_records_contributing_factors() -> None:
    incident = IncidentExtraction.model_validate({
        "incident_type": "unauthorized_access",
        "affected_assets": ["production database"],
        "data_sensitivity": "regulated",
        "users_affected": 1200,
        "service_disruption_hours": 25,
        "cve_ids": ["CVE-2024-1234"],
        "iocs": [],
        "contained": False,
        "external_source": True,
        "summary": "Unauthorized access was confirmed.",
    })
    assessment = analyze_risk(incident, RULES, alert_count=2, cve_cvss={"CVE-2024-1234": 9.8})
    assert assessment.likelihood == 5
    assert assessment.impact == 5
    assert assessment.score == 10
    assert assessment.band == "Critical"
    assert any("External source" in factor for factor in assessment.likelihood_factors)
