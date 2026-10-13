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
