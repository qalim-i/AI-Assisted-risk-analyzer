"""Validation helpers for source-traceable incident extraction."""

from __future__ import annotations

import re
import unicodedata

from schema import IncidentExtraction


def normalize_for_match(value: str) -> str:
    """Normalize case, Unicode, and whitespace before source-text matching."""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", "", normalized)


def validate_traceability(incident: IncidentExtraction, source_text: str) -> list[str]:
    """Return warnings for CVEs and IoCs that do not occur in ``source_text``.

    Checks are deliberately conservative: data remains available for review while
    untraceable fields are reported rather than silently discarded.
    """
    source = normalize_for_match(source_text)
    warnings: list[str] = []
    for cve in incident.cve_ids:
        if normalize_for_match(cve) not in source:
            warnings.append(f"CVE '{cve}' could not be traced to the input text.")
    for ioc in incident.iocs:
        if normalize_for_match(ioc.value) not in source:
            warnings.append(f"IoC ({ioc.type.value}) '{ioc.value}' could not be traced to the input text.")
    return warnings


def validate_data_quality(incident: IncidentExtraction, source_text: str) -> list[str]:
    """Return traceability and source-completeness notes for a report.

    The extractor is intentionally limited to facts that occur in the input.  A
    clean traceability check therefore does not mean that an incident description
    contains every fact useful for a risk decision.  These notes make omitted
    fields visible without treating them as facts or changing the risk score.
    """
    warnings = validate_traceability(incident, source_text)
    completeness_checks = (
        (not incident.affected_assets, "Affected assets were not stated; asset criticality uses the default value."),
        (incident.data_sensitivity is None, "Data sensitivity was not stated; data-impact scoring may be incomplete."),
        (incident.users_affected is None, "Affected-user count was not stated; user-impact scoring may be incomplete."),
        (incident.service_disruption_hours is None, "Service-disruption duration was not stated; availability impact may be incomplete."),
        (incident.detection_source is None, "Detection source was not stated; the alert evidence cannot be assessed."),
        (incident.contained is None, "Containment status was not stated; the likelihood score cannot reflect containment."),
        (incident.external_source is None, "External-source status was not stated; the likelihood score may be incomplete."),
    )
    warnings.extend(note for missing, note in completeness_checks if missing)
    return warnings
