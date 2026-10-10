import os
import re
import subprocess
import shutil
import yaml

_REF_PATH = os.path.join(os.path.dirname(__file__), "crypto_library_versions.yaml")
WEAK_INDICATOR_RE = re.compile(r"\b(MD5|DES|RC4)\b")


def _load_reference():
    with open(_REF_PATH, "r") as f:
        return yaml.safe_load(f)["libraries"]


def _run_strings(path: str):
    if shutil.which("strings") is None:
        # Fallback: crude ASCII extraction if `strings` binary isn't installed
        try:
            with open(path, "rb") as f:
                data = f.read()
            ascii_runs = re.findall(rb"[\x20-\x7e]{5,}", data)
            return b"\n".join(ascii_runs).decode("ascii", errors="ignore")
        except OSError:
            return ""
    try:
        result = subprocess.run(["strings", path], capture_output=True, text=True, timeout=30)
        return result.stdout
    except (subprocess.SubprocessError, OSError):
        return ""


def scan_binary(path: str):
    """Scan a single binary file for embedded crypto library banners."""
    findings = []
    output = _run_strings(path)
    if not output:
        return findings

    reference = _load_reference()
    seen_libs = set()
    for entry in reference:
        if entry["match"] in output and entry["name"] not in seen_libs:
            seen_libs.add(entry["name"])
            findings.append({
                "file": os.path.basename(path),
                "line": None,
                "language": None,
                "algorithm": entry["name"],
                "mode": None,
                "key_size": None,
                "category": "library",
                "severity_hint": "medium" if entry["quantum_vulnerable_default"] else "low",
                "raw_snippet": f"matched banner '{entry['match']}'; {entry['note']}"[:300],
                "asset_type": "binary_embedded_lib",
            })

    weak_hits = set(WEAK_INDICATOR_RE.findall(output))
    for algo in weak_hits:
        findings.append({
            "file": os.path.basename(path),
            "line": None,
            "language": None,
            "algorithm": algo,
            "mode": None,
            "key_size": None,
            "category": "symmetric" if algo != "MD5" else "hash",
            "severity_hint": "high",
            "raw_snippet": f"weak-algorithm string indicator '{algo}' found in binary symbols",
            "asset_type": "binary_embedded_lib",
        })
    return findings


def scan_binaries_dir(root: str):
    """Walk a directory scanning every regular file as a candidate binary."""
    findings = []
    for dirpath, _, filenames in os.walk(root):
        if "/.git" in dirpath:
            continue
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            findings.extend(scan_binary(fpath))
    return findings
