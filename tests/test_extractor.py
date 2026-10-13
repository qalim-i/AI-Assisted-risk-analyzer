import json

from extractor import extract_incident


def test_extractor_parses_mocked_llm_json(monkeypatch) -> None:
    payload = {
        "incident_type": "phishing",
        "other_type_description": None,
        "affected_assets": ["email gateway"],
        "data_sensitivity": None,
        "users_affected": None,
        "service_disruption_hours": None,
        "cve_ids": [],
        "iocs": [{"type": "domain", "value": "login-bad.example"}],
        "detection_source": "user report",
        "contained": True,
        "external_source": True,
        "summary": "A phishing email was reported.",
    }
    monkeypatch.setattr("extractor.complete", lambda prompt, system: json.dumps(payload))
    result = extract_incident("A user reported login-bad.example in a phishing email.")
    assert result.incident_type.value == "phishing"
    assert result.iocs[0].value == "login-bad.example"
