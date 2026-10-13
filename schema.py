"""Pydantic models used by the incident analyzer."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IncidentType(str, Enum):
    """Supported incident categories."""

    phishing = "phishing"
    malware = "malware"
    unauthorized_access = "unauthorized_access"
    data_exposure = "data_exposure"
    denial_of_service = "denial_of_service"
    other = "other"


class DataSensitivity(str, Enum):
    """Sensitivity levels used by the risk rules."""

    none = "none"
    internal = "internal"
    confidential = "confidential"
    regulated = "regulated"


class IocType(str, Enum):
    """Indicator types that can be validated against source text."""

    ip = "ip"
    domain = "domain"
    hash = "hash"
    url = "url"
    cve = "cve"


class IndicatorOfCompromise(BaseModel):
    """One source-traceable indicator of compromise."""

    model_config = ConfigDict(extra="forbid")

    type: IocType
    value: str = Field(min_length=1, max_length=2_048)


class IncidentExtraction(BaseModel):
    """Structured facts extracted from an incident description.

    Optional fields must be ``null`` when the source text does not state them.
    """

    model_config = ConfigDict(extra="forbid")

    incident_type: IncidentType
    other_type_description: str | None = None
    affected_assets: list[str] = Field(default_factory=list)
    data_sensitivity: DataSensitivity | None = None
    users_affected: int | None = Field(default=None, ge=0)
    service_disruption_hours: float | None = Field(default=None, ge=0)
    cve_ids: list[str] = Field(default_factory=list)
    iocs: list[IndicatorOfCompromise] = Field(default_factory=list)
    detection_source: str | None = None
    contained: bool | None = None
    external_source: bool | None = None
    summary: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_other_type(self) -> "IncidentExtraction":
        """Require a description only when ``incident_type`` is ``other``."""
        if self.incident_type is IncidentType.other and not self.other_type_description:
            raise ValueError("other_type_description is required when incident_type is 'other'")
        if self.incident_type is not IncidentType.other and self.other_type_description:
            raise ValueError("other_type_description is only allowed when incident_type is 'other'")
        return self
