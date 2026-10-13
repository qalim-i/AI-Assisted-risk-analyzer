import pytest
from pydantic import ValidationError

from schema import IncidentExtraction


def test_schema_rejects_out_of_range_values() -> None:
    with pytest.raises(ValidationError):
        IncidentExtraction.model_validate({
            "incident_type": "phishing",
            "affected_assets": [],
            "users_affected": -1,
            "service_disruption_hours": -0.5,
            "cve_ids": [],
            "iocs": [],
            "contained": False,
            "summary": "A phishing email was reported.",
        })
