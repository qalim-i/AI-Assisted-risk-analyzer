from schema import IncidentExtraction
from validator import validate_data_quality, validate_traceability


def incident_with_iocs() -> IncidentExtraction:
    return IncidentExtraction.model_validate({
        "incident_type": "malware",
        "affected_assets": ["employee workstation"],
        "data_sensitivity": "internal",
        "cve_ids": ["CVE-2024-1234"],
        "iocs": [{"type": "ip", "value": "203.0.113.10"}, {"type": "domain", "value": "evil.example"}],
        "contained": True,
        "summary": "Malware was found.",
    })


def test_iocs_are_valid_when_present_after_normalization() -> None:
    text = "Observed CVE-2024-1234 and connection to 203.0.113.10. EVIL.EXAMPLE was blocked."
    assert validate_traceability(incident_with_iocs(), text) == []


def test_iocs_are_warned_when_not_present() -> None:
    warnings = validate_traceability(incident_with_iocs(), "Only 203.0.113.10 appears here.")
    assert len(warnings) == 2
    assert "CVE-2024-1234" in warnings[0]
    assert "evil.example" in warnings[1]


def test_data_quality_flags_only_missing_source_facts() -> None:
    incident = IncidentExtraction.model_validate({
        "incident_type": "malware",
        "affected_assets": ["employee workstation"],
        "data_sensitivity": "internal",
        "users_affected": 1,
        "service_disruption_hours": 0,
        "detection_source": "endpoint protection",
        "contained": True,
        "external_source": False,
        "summary": "Endpoint protection blocked suspicious activity.",
    })
    assert validate_data_quality(incident, "Endpoint protection blocked suspicious activity.") == []


def test_data_quality_warns_about_omitted_fields() -> None:
    incident = IncidentExtraction.model_validate({
        "incident_type": "phishing",
        "affected_assets": ["email gateway"],
        "contained": True,
        "summary": "A phishing message was blocked.",
    })
    warnings = validate_data_quality(incident, "A phishing message was blocked.")
    assert any("Data sensitivity" in warning for warning in warnings)
    assert any("Affected-user count" in warning for warning in warnings)
    assert any("Service-disruption" in warning for warning in warnings)
    assert not any("Containment status" in warning for warning in warnings)
