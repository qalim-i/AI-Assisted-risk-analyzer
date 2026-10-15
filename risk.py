"""Deterministic, configurable risk scoring for incident facts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from schema import IncidentExtraction


@dataclass(frozen=True)
class RiskAssessment:
    """Transparent risk score and the factors used to calculate it."""

    likelihood: int
    impact: int
    score: int
    band: str
    likelihood_factors: list[str]
    impact_factors: list[str]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "likelihood": self.likelihood,
            "impact": self.impact,
            "score": self.score,
            "band": self.band,
            "likelihood_factors": self.likelihood_factors,
            "impact_factors": self.impact_factors,
        }


def load_rules(path: str | Path) -> dict[str, Any]:
    """Load and minimally validate a YAML risk-rule configuration."""
    with Path(path).open("r", encoding="utf-8") as handle:
        rules = yaml.safe_load(handle)
    if not isinstance(rules, dict) or not {"likelihood", "impact", "bands"} <= rules.keys():
        raise ValueError("rules.yaml must define likelihood, impact, and bands sections")
    return rules


def risk_band(score: int, bands: Mapping[str, int]) -> str:
    """Map a 2--10 risk score to its configured severity band."""
    if score <= bands["low_max"]:
        return "Low"
    if score <= bands["medium_max"]:
        return "Medium"
    if score <= bands["high_max"]:
        return "High"
    return "Critical"


def _band_points(value: float | int | None, bands: list[dict[str, Any]]) -> tuple[int, str] | None:
    if value is None:
        return None
    selected = None
    for band in bands:
        if value >= band["minimum"]:
            selected = (int(band["points"]), str(band["label"]))
    return selected


def _asset_points(assets: list[str], criticality: Mapping[str, int]) -> tuple[int, str]:
    joined = " ".join(assets).lower()
    matches = [(name, int(points)) for name, points in criticality.items() if name != "default" and name in joined]
    if matches:
        name, points = max(matches, key=lambda item: item[1])
        return points, name
    return int(criticality.get("default", 0)), "default asset criticality"


def analyze_risk(
    incident: IncidentExtraction,
    rules_path: str | Path,
    *,
    alert_count: int = 0,
    cve_cvss: Mapping[str, float] | None = None,
) -> RiskAssessment:
    """Score an incident using only supplied facts and the editable YAML rules.

    ``alert_count`` represents corroborating alert records; values above one count
    as repeated events. ``cve_cvss`` is an optional, caller-provided lookup table.
    """
    rules = load_rules(rules_path)
    likelihood_rules = rules["likelihood"]
    impact_rules = rules["impact"]
    likelihood = int(likelihood_rules["base"])
    likelihood_factors = [f"Base likelihood: {likelihood}"]

    if incident.external_source is True:
        points = int(likelihood_rules["external_source"])
        likelihood += points
        likelihood_factors.append(f"External source: +{points}")
    high_cves = [cve for cve in incident.cve_ids if cve_cvss and cve_cvss.get(cve.upper(), 0) >= 7.0]
    if high_cves:
        points = int(likelihood_rules["high_cvss_cve"])
        likelihood += points
        likelihood_factors.append(f"CVSS ≥ 7.0 ({', '.join(high_cves)}): +{points}")
    if alert_count > 1:
        points = int(likelihood_rules["repeated_events"])
        likelihood += points
        likelihood_factors.append(f"Repeated alert events ({alert_count}): +{points}")
    if incident.contained is True:
        points = int(likelihood_rules["contained_reduction"])
        likelihood -= points
        likelihood_factors.append(f"Contained: -{points}")
    likelihood = max(int(likelihood_rules["minimum"]), min(likelihood, int(likelihood_rules["maximum"])))

    impact = int(impact_rules["base"])
    impact_factors = [f"Base impact: {impact}"]
    if incident.data_sensitivity is not None:
        points = int(impact_rules["data_sensitivity"][incident.data_sensitivity.value])
        impact += points
        impact_factors.append(f"Data sensitivity ({incident.data_sensitivity.value}): +{points}")
    for value, key, label in ((incident.users_affected, "users_affected", "Users affected"), (incident.service_disruption_hours, "disruption_hours", "Service disruption")):
        result = _band_points(value, impact_rules[key])
        if result:
            points, band_label = result
            impact += points
            impact_factors.append(f"{label} ({band_label}): +{points}")
    points, asset = _asset_points(incident.affected_assets, impact_rules["asset_criticality"])
    impact += points
    impact_factors.append(f"Asset criticality ({asset}): +{points}")
    impact = min(impact, int(impact_rules["maximum"]))

    score = likelihood + impact
    return RiskAssessment(likelihood, impact, score, risk_band(score, rules["bands"]), likelihood_factors, impact_factors)
