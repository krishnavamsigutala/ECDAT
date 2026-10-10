from app.detectors.generic_scan import scan_dir


def scan_go_dir(root: str):
    return scan_dir(root, "go", (".go",))
