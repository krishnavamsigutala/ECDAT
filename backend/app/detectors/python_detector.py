import os
import re
from app.detectors.rules_loader import compiled

KEY_SIZE_RE = re.compile(r"(\d{3,5})")
MODE_RE = re.compile(r"MODE_([A-Z0-9]+)")


def scan_python_dir(root: str):
    """Walk `root` for .py files and return normalized finding dicts."""
    findings = []
    rules = compiled("python")
    for dirpath, _, filenames in os.walk(root):
        if "/.git" in dirpath or "/node_modules" in dirpath:
            continue
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, "r", errors="ignore") as f:
                    lines = f.readlines()
            except OSError:
                continue

            for lineno, line in enumerate(lines, start=1):
                for rule, pattern in rules:
                    m = pattern.search(line)
                    if not m:
                        continue
                    key_size = None
                    mode = None
                    if rule["algorithm_name"] == "RSA":
                        ks = KEY_SIZE_RE.search(line)
                        if ks:
                            key_size = int(ks.group(1))
                    mode_m = MODE_RE.search(line)
                    if mode_m:
                        mode = mode_m.group(1)
                    findings.append({
                        "file": os.path.relpath(fpath, root),
                        "line": lineno,
                        "language": "python",
                        "algorithm": rule["algorithm_name"],
                        "mode": mode,
                        "key_size": key_size,
                        "category": rule["category"],
                        "severity_hint": rule["severity_hint"],
                        "raw_snippet": line.strip()[:200],
                        "asset_type": "algorithm" if rule["category"] != "library" else "library",
                    })
    return findings
