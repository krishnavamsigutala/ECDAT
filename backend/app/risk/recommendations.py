import os
import json
import yaml

_MAPPING_PATH = os.path.join(os.path.dirname(__file__), "pqc_mapping.yaml")
_cache = None


def _load():
    global _cache
    if _cache is None:
        with open(_MAPPING_PATH, "r") as f:
            _cache = yaml.safe_load(f)
    return _cache


def get_recommendation(algorithm: str, risk_level: str) -> dict:
    data = _load()
    mapping = data["mappings"].get(algorithm, data["default"])
    use_hybrid = risk_level in ("Critical", "High")
    return {
        "algorithm": algorithm,
        "risk_level": risk_level,
        "recommended_form": "hybrid" if use_hybrid else "single",
        "recommendation": mapping["hybrid"] if use_hybrid else mapping["single"],
        "latency_impact": mapping["latency_impact"],
        "size_impact": mapping["size_impact"],
        "library_maturity": mapping["library_maturity"],
        "rationale": mapping["rationale"],
    }


def get_recommendation_summary(algorithm: str, risk_level: str) -> str:
    rec = get_recommendation(algorithm, risk_level)
    return rec["recommendation"]


def get_recommendation_json(algorithm: str, risk_level: str) -> str:
    return json.dumps(get_recommendation(algorithm, risk_level))
