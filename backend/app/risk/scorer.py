import os
import yaml
from app.risk.mosca import calculate_mosca_risk
from app.risk.criticality import get_defaults
from app.risk.recommendations import get_recommendation, get_recommendation_json

_REF_PATH = os.path.join(os.path.dirname(__file__), "quantum_reference.yaml")
_cache = None


def _load_reference():
    global _cache
    if _cache is None:
        with open(_REF_PATH, "r") as f:
            _cache = yaml.safe_load(f)
    return _cache


def lookup_quantum_status(algorithm: str) -> dict:
    data = _load_reference()
    return data["algorithms"].get(algorithm, data["default"])


def score_asset(algorithm: str, criticality_tag: str, global_z: float) -> dict:
    """Compute full risk scoring for one crypto asset. Returns a dict ready to
    populate a Finding row (minus asset_id)."""
    q = lookup_quantum_status(algorithm)
    defaults = get_defaults(criticality_tag)
    x, y = defaults["x"], defaults["y"]

    mosca = calculate_mosca_risk(x, y, global_z)
    quantum_vulnerable = bool(q["quantum_vulnerable"])
    at_risk = mosca["at_risk"]
    high_criticality = defaults["weight"] == "high"

    if quantum_vulnerable and at_risk and high_criticality:
        risk_level = "Critical"
    elif quantum_vulnerable and at_risk:
        risk_level = "High"
    elif quantum_vulnerable and not at_risk:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    explanation = (
        f"{algorithm} is {'quantum-vulnerable (' + str(q['broken_by']) + ')' if quantum_vulnerable else 'not quantum-vulnerable'}. "
        f"{mosca['explanation']} Criticality tag '{criticality_tag}' (X={x}y, Y={y}y)."
    )

    rec = get_recommendation(algorithm, risk_level)

    return {
        "quantum_vulnerable": quantum_vulnerable,
        "broken_by": q.get("broken_by"),
        "risk_level": risk_level,
        "mosca_x": x,
        "mosca_y": y,
        "mosca_z": global_z,
        "at_risk": at_risk,
        "explanation": explanation,
        "recommendation_summary": rec["recommendation"],
        "recommendation_detail": get_recommendation_json(algorithm, risk_level),
    }
