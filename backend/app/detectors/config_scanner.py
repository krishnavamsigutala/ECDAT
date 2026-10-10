import os
import re

CONFIG_FILENAMES = {
    "nginx.conf", "httpd.conf", "application.yml", "application.yaml",
    "application.properties", "web.xml",
}

WEAK_PROTOCOL_RE = re.compile(r"(SSLv2|SSLv3|TLSv1\.0|TLSv1\.1|TLSv1(?![.\d]))", re.IGNORECASE)
DIRECTIVE_RE = re.compile(r"(ssl_protocols|sslEnabledProtocols|sslprotocol)", re.IGNORECASE)
WEAK_CIPHER_RE = re.compile(r"\b(RC4|DES|EXPORT|NULL|MD5)\b")


def scan_configs_dir(root: str):
    findings = []
    for dirpath, _, filenames in os.walk(root):
        if "/.git" in dirpath or "/node_modules" in dirpath:
            continue
        for fname in filenames:
            if fname not in CONFIG_FILENAMES:
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, "r", errors="ignore") as f:
                    lines = f.readlines()
            except OSError:
                continue

            for lineno, line in enumerate(lines, start=1):
                if DIRECTIVE_RE.search(line) and WEAK_PROTOCOL_RE.search(line):
                    findings.append({
                        "file": os.path.relpath(fpath, root),
                        "line": lineno,
                        "language": "config",
                        "algorithm": "Weak TLS protocol version",
                        "mode": None,
                        "key_size": None,
                        "category": "protocol",
                        "severity_hint": "high",
                        "raw_snippet": line.strip()[:200],
                        "asset_type": "protocol",
                    })
                if WEAK_CIPHER_RE.search(line) and ("cipher" in line.lower() or "Cipher" in line):
                    findings.append({
                        "file": os.path.relpath(fpath, root),
                        "line": lineno,
                        "language": "config",
                        "algorithm": "Weak cipher suite",
                        "mode": None,
                        "key_size": None,
                        "category": "protocol",
                        "severity_hint": "high",
                        "raw_snippet": line.strip()[:200],
                        "asset_type": "protocol",
                    })
    return findings
