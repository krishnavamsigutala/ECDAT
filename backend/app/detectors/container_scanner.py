import json
import shutil
import subprocess

CRYPTO_LIBRARY_KEYWORDS = (
    "openssl", "libssl", "bouncycastle", "cryptography", "pyopenssl",
    "node-forge", "libcrypto", "mbedtls", "libsodium", "wolfssl", "boringssl",
)


def scan_container_image(image_ref: str):
    """Run Syft against a container image reference and filter for crypto-relevant packages.

    Gracefully returns an empty list (rather than raising) if Syft is not
    installed in this environment — e.g. when running outside the packaged
    Docker image.
    """
    if shutil.which("syft") is None:
        return []

    try:
        result = subprocess.run(
            ["syft", image_ref, "-o", "json"],
            capture_output=True, text=True, timeout=180,
        )
    except (subprocess.SubprocessError, OSError):
        return []

    if result.returncode != 0 or not result.stdout:
        return []

    try:
        sbom = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    findings = []
    for artifact in sbom.get("artifacts", []):
        name = (artifact.get("name") or "").lower()
        if not any(k in name for k in CRYPTO_LIBRARY_KEYWORDS):
            continue
        findings.append({
            "file": image_ref,
            "line": None,
            "language": None,
            "algorithm": artifact.get("name"),
            "mode": None,
            "key_size": None,
            "category": "library",
            "severity_hint": "medium",
            "raw_snippet": f"version={artifact.get('version')}; type={artifact.get('type')}"[:200],
            "asset_type": "container_library",
        })
    return findings
