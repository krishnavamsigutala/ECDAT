import os
import shutil
import tempfile
import zipfile
import traceback

from app.database import SessionLocal
from app import models
from app.detectors import engine as detection_engine
from app.risk.scorer import score_asset
from app.risk.criticality import DEFAULT_TAG


def _get_global_z(db) -> float:
    row = db.query(models.Settings).filter(models.Settings.key == "mosca_z").first()
    if row:
        return float(row.value)
    return 10.0


def _persist_findings(db, scan_run_id: int, raw_findings: list, global_z: float):
    for rf in raw_findings:
        asset = models.CryptoAsset(
            scan_run_id=scan_run_id,
            asset_type=rf.get("asset_type", "algorithm"),
            name=rf.get("algorithm"),
            algorithm=rf.get("algorithm"),
            category=rf.get("category"),
            key_size=rf.get("key_size"),
            mode=rf.get("mode"),
            language=rf.get("language"),
            source_file=rf.get("file"),
            line_number=rf.get("line"),
            raw_snippet=rf.get("raw_snippet"),
            criticality_tag=DEFAULT_TAG,
        )
        db.add(asset)
        db.flush()  # get asset.id

        score = score_asset(asset.algorithm or "unknown", asset.criticality_tag, global_z)
        finding = models.Finding(asset_id=asset.id, **score)
        db.add(finding)
    db.commit()


def run_scan(scan_run_id: int):
    db = SessionLocal()
    tmp_dir = None
    try:
        scan = db.query(models.ScanRun).filter(models.ScanRun.id == scan_run_id).first()
        if not scan:
            return
        scan.status = "running"
        scan.progress_message = "Resolving target"
        db.commit()

        global_z = _get_global_z(db)
        raw_findings = []

        if scan.target_type == "repo":
            scan.progress_message = "Cloning repository"
            db.commit()
            tmp_dir = tempfile.mkdtemp(prefix="ecdat_repo_")
            try:
                import git
                git.Repo.clone_from(scan.target_ref, tmp_dir, depth=1)
            except Exception as e:
                raise RuntimeError(f"Failed to clone repo: {e}")
            scan.progress_message = "Scanning source code"
            db.commit()
            raw_findings = detection_engine.run_source_scan(tmp_dir)

        elif scan.target_type == "zip":
            scan.progress_message = "Extracting archive"
            db.commit()
            tmp_dir = tempfile.mkdtemp(prefix="ecdat_zip_")
            with zipfile.ZipFile(scan.target_ref, "r") as zf:
                zf.extractall(tmp_dir)
            scan.progress_message = "Scanning source code"
            db.commit()
            raw_findings = detection_engine.run_source_scan(tmp_dir)

        elif scan.target_type == "local":
            scan.progress_message = "Scanning local directory"
            db.commit()
            raw_findings = detection_engine.run_source_scan(scan.target_ref)
            raw_findings += detection_engine.run_binary_dir_scan(scan.target_ref)

        elif scan.target_type == "binary":
            scan.progress_message = "Scanning binary"
            db.commit()
            raw_findings = detection_engine.run_binary_file_scan(scan.target_ref)

        elif scan.target_type == "image":
            scan.progress_message = "Generating SBOM via Syft"
            db.commit()
            raw_findings = detection_engine.run_container_scan(scan.target_ref)

        else:
            raise ValueError(f"Unknown target_type: {scan.target_type}")

        scan.progress_message = f"Scoring {len(raw_findings)} findings"
        db.commit()
        _persist_findings(db, scan_run_id, raw_findings, global_z)

        scan.status = "completed"
        scan.progress_message = f"Completed — {len(raw_findings)} crypto assets found"
        import datetime
        scan.completed_at = datetime.datetime.utcnow()
        db.commit()

    except Exception as e:
        db.rollback()
        scan = db.query(models.ScanRun).filter(models.ScanRun.id == scan_run_id).first()
        if scan:
            scan.status = "failed"
            scan.error_message = f"{e}\n{traceback.format_exc()[-1500:]}"
            scan.progress_message = "Failed"
            db.commit()
    finally:
        db.close()
        if tmp_dir and os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
