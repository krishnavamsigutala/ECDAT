from app.detectors.generic_scan import scan_dir


def scan_js_dir(root: str):
    return scan_dir(root, "javascript", (".js", ".ts", ".jsx", ".tsx"))
