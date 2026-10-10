import os
import re
import yaml

_RULES_PATH = os.path.join(os.path.dirname(__file__), "rules.yaml")
_cache = None


def load_rules(language: str = None):
    global _cache
    if _cache is None:
        with open(_RULES_PATH, "r") as f:
            data = yaml.safe_load(f)
        _cache = data.get("rules", [])
    if language:
        return [r for r in _cache if r["language"] == language]
    return _cache


def compiled(language: str):
    """Return list of (rule, compiled_regex) for a language."""
    out = []
    for r in load_rules(language):
        out.append((r, re.compile(r["pattern"])))
    return out
