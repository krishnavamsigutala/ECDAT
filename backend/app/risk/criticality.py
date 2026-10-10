CRITICALITY_DEFAULTS = {
    "public_internet_facing": {"x": 8, "y": 2, "weight": "high"},
    "internal_only": {"x": 5, "y": 1, "weight": "medium"},
    "stores_sensitive_data": {"x": 15, "y": 2.5, "weight": "high"},
    "long_term_archival": {"x": 25, "y": 3, "weight": "high"},
}

DEFAULT_TAG = "internal_only"


def get_defaults(tag: str) -> dict:
    return CRITICALITY_DEFAULTS.get(tag, CRITICALITY_DEFAULTS[DEFAULT_TAG])
