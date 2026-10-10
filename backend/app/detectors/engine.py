from app.detectors.python_detector import scan_python_dir
from app.detectors.java_detector import scan_java_dir
from app.detectors.c_detector import scan_c_dir
from app.detectors.js_detector import scan_js_dir
from app.detectors.go_detector import scan_go_dir
from app.detectors.cert_scanner import scan_certs_dir
from app.detectors.config_scanner import scan_configs_dir
from app.detectors.binary_scanner import scan_binaries_dir, scan_binary
from app.detectors.container_scanner import scan_container_image


def run_source_scan(root: str):
    """Run every source/cert/config detector over a directory tree."""
    findings = []
    findings.extend(scan_python_dir(root))
    findings.extend(scan_java_dir(root))
    findings.extend(scan_c_dir(root))
    findings.extend(scan_js_dir(root))
    findings.extend(scan_go_dir(root))
    findings.extend(scan_certs_dir(root))
    findings.extend(scan_configs_dir(root))
    return findings


def run_binary_dir_scan(root: str):
    return scan_binaries_dir(root)


def run_binary_file_scan(path: str):
    return scan_binary(path)


def run_container_scan(image_ref: str):
    return scan_container_image(image_ref)
