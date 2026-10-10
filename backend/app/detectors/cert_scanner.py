import os
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, ec, dsa

CERT_EXTENSIONS = (".pem", ".crt", ".cer", ".der")


def _algo_and_keysize(public_key):
    if isinstance(public_key, rsa.RSAPublicKey):
        return "RSA", public_key.key_size
    if isinstance(public_key, ec.EllipticCurvePublicKey):
        return "ECDSA", public_key.key_size
    if isinstance(public_key, dsa.DSAPublicKey):
        return "DSA", public_key.key_size
    return type(public_key).__name__, None


def scan_certs_dir(root: str):
    findings = []
    for dirpath, _, filenames in os.walk(root):
        if "/.git" in dirpath or "/node_modules" in dirpath:
            continue
        for fname in filenames:
            if not fname.endswith(CERT_EXTENSIONS):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, "rb") as f:
                    raw = f.read()
            except OSError:
                continue

            cert = None
            for loader in (x509.load_pem_x509_certificate, x509.load_der_x509_certificate):
                try:
                    cert = loader(raw, default_backend())
                    break
                except Exception:
                    continue
            if cert is None:
                continue  # not a parseable cert, skip gracefully

            try:
                algo, key_size = _algo_and_keysize(cert.public_key())
                sig_algo = cert.signature_hash_algorithm.name.upper() if cert.signature_hash_algorithm else "unknown"
                findings.append({
                    "file": os.path.relpath(fpath, root),
                    "line": None,
                    "language": None,
                    "algorithm": algo,
                    "mode": None,
                    "key_size": key_size,
                    "category": "asymmetric",
                    "severity_hint": "critical" if algo in ("RSA", "ECDSA", "DSA") else "low",
                    "raw_snippet": (
                        f"subject={cert.subject.rfc4514_string()}; issuer={cert.issuer.rfc4514_string()}; "
                        f"sig_algo={sig_algo}; not_valid_after={cert.not_valid_after_utc.isoformat()}; "
                        f"serial={cert.serial_number}"
                    )[:400],
                    "asset_type": "certificate",
                })
            except Exception:
                continue  # malformed cert field, skip gracefully
    return findings
