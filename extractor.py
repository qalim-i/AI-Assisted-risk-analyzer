"""LLM-based extraction with schema-constrained JSON parsing."""

from __future__ import annotations

import json

from pydantic import ValidationError

from llm import complete
from schema import IncidentExtraction


class ExtractionError(RuntimeError):
    """Raised after the LLM cannot return a valid extraction twice."""


def _json_payload(response: str) -> dict[str, object]:
    """Parse a JSON object, tolerating an accidental Markdown code fence."""
    candidate = response.strip()
    if candidate.startswith("```"):
        candidate = candidate.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("The response was not a JSON object.")
    return parsed


def extract_incident(description: str) -> IncidentExtraction:
    """Extract source-grounded incident facts, retrying once on invalid JSON."""
    if not description.strip():
        raise ValueError("An incident description is required for extraction.")
    schema = json.dumps(IncidentExtraction.model_json_schema(), indent=2)
    system = "You extract cybersecurity incident facts precisely. Never invent facts."
    prompt = (
        "Return ONLY a JSON object matching this JSON Schema. Use null for every field "
        "whose value is not explicitly stated. Only include IoCs and CVE IDs that occur "
        "in the incident description.\n\nJSON Schema:\n"
        f"{schema}\n\nIncident description:\n{description}"
    )
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = complete(prompt, system)
            return IncidentExtraction.model_validate(_json_payload(response))
        except (json.JSONDecodeError, ValidationError, ValueError, RuntimeError) as error:
            last_error = error
            prompt += "\n\nYour previous response was invalid. Return only a complete JSON object matching the schema."
    raise ExtractionError(f"The LLM returned invalid incident data after two attempts: {last_error}") from last_error
