"""Runs a scan against each bundled demo project so judges see populated
data immediately on `docker compose up`, without waiting for a live clone.
Safe to re-run: it only seeds when no scans exist yet.
"""
import os
import time
import requests

BASE = os.getenv("ECDAT_API_BASE", "http://localhost:8000")
DEMO_TARGETS = [
    "demo/weak_python_app",
    "demo/weak_java_app",
    "demo/strong_app",
]


def wait_for_backend(timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{BASE}/health", timeout=2)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


def already_seeded():
    try:
        r = requests.get(f"{BASE}/scans", timeout=5)
        return r.status_code == 200 and len(r.json()) > 0
    except requests.RequestException:
        return False


def seed():
    if not wait_for_backend():
        print("Backend did not come up in time — skipping seed.")
        return
    if already_seeded():
        print("Scans already present — skipping seed.")
        return

    for target in DEMO_TARGETS:
        r = requests.post(f"{BASE}/scan/local", json={"target_type": "local", "target_ref": target})
        r.raise_for_status()
        scan_id = r.json()["id"]
        print(f"Seeding scan #{scan_id} for {target}...")
        for _ in range(30):
            status = requests.get(f"{BASE}/scan/{scan_id}/status", timeout=5).json()
            if status["status"] in ("completed", "failed"):
                print(f"  -> {status['status']}: {status['progress_message']}")
                break
            time.sleep(1)


if __name__ == "__main__":
    seed()
