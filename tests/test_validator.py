from schema import IncidentExtraction
from validator import validate_traceability


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
