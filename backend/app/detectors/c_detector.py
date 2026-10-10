from app.detectors.generic_scan import scan_dir


def scan_c_dir(root: str):
    return scan_dir(root, "c", (".c", ".cpp", ".h", ".hpp", ".cc"))
