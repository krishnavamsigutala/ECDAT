from app.detectors.generic_scan import scan_dir


def scan_java_dir(root: str):
    return scan_dir(root, "java", (".java",))
