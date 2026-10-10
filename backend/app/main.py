import os
import shutil
import tempfile
from collections import Counter
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models, schemas
from app.orchestrator import run_scan
from app.risk.criticality import CRITICALITY_DEFAULTS
from app.risk.recommendations import get_recommendation
from app.reports.cbom_generator import generate_cbom_dict
from app.reports.pdf_report import generate_pdf_report

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ECDAT — Enterprise Cryptographic Discovery & Analysis Tool")

origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/tmp/ecdat_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Scan lifecycle
# ---------------------------------------------------------------------------

@app.post("/scan", response_model=schemas.ScanStatus)
def create_scan(payload: schemas.ScanCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if payload.target_type not in ("repo", "zip", "image", "binary", "local"):
        raise HTTPException(400, "invalid target_type")
    scan = models.ScanRun(target_type=payload.target_type, target_ref=payload.target_ref, status="pending")
    db.add(scan)
    db.commit()
    db.refresh(scan)
    background_tasks.add_task(run_scan, scan.id)
    return scan


@app.post("/scan/upload", response_model=schemas.ScanStatus)
def create_scan_from_upload(
    background_tasks: BackgroundTasks,
    target_type: str = Query(..., description="zip or binary"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if target_type not in ("zip", "binary"):
        raise HTTPException(400, "target_type must be zip or binary for uploads")
    dest_path = os.path.join(UPLOAD_DIR, f"{next(tempfile._get_candidate_names())}_{file.filename}")
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    scan = models.ScanRun(target_type=target_type, target_ref=dest_path, status="pending")
    db.add(scan)
    db.commit()
    db.refresh(scan)
    background_tasks.add_task(run_scan, scan.id)
    return scan


@app.post("/scan/local", response_model=schemas.ScanStatus)
def create_scan_local(payload: schemas.ScanCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Convenience endpoint for testing against a local folder path (e.g. test_fixtures/)."""
    scan = models.ScanRun(target_type="local", target_ref=payload.target_ref, status="pending")
    db.add(scan)
    db.commit()
    db.refresh(scan)
    background_tasks.add_task(run_scan, scan.id)
    return scan


@app.get("/scan/{scan_id}/status", response_model=schemas.ScanStatus)
def get_scan_status(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(models.ScanRun).filter(models.ScanRun.id == scan_id).first()
    if not scan:
        raise HTTPException(404, "scan not found")
    return scan


@app.get("/scan/{scan_id}/results")
def get_scan_results(
    scan_id: int,
    risk_level: Optional[str] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    scan = db.query(models.ScanRun).filter(models.ScanRun.id == scan_id).first()
    if not scan:
        raise HTTPException(404, "scan not found")

    q = db.query(models.CryptoAsset).filter(models.CryptoAsset.scan_run_id == scan_id)
    if category:
        q = q.filter(models.CryptoAsset.category == category)
    if language:
        q = q.filter(models.CryptoAsset.language == language)
    assets = q.all()

    if risk_level:
        assets = [a for a in assets if a.finding and a.finding.risk_level == risk_level]

    total = len(assets)
    start = (page - 1) * page_size
    page_assets = assets[start:start + page_size]

    return {
        "scan_id": scan_id,
        "status": scan.status,
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": [schemas.AssetOut.model_validate(a).model_dump() for a in page_assets],
    }


@app.get("/scans")
def list_scans(db: Session = Depends(get_db)):
    scans = db.query(models.ScanRun).order_by(models.ScanRun.created_at.desc()).all()
    out = []
    for s in scans:
        counts = Counter(a.finding.risk_level for a in s.assets if a.finding)
        out.append({
            "id": s.id,
            "target_type": s.target_type,
            "target_ref": s.target_ref,
            "status": s.status,
            "created_at": s.created_at,
            "counts": {lvl: counts.get(lvl, 0) for lvl in ("Critical", "High", "Medium", "Low")},
            "total_assets": len(s.assets),
        })
    return out


@app.delete("/scan/{scan_id}")
def delete_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(models.ScanRun).filter(models.ScanRun.id == scan_id).first()
    if not scan:
        raise HTTPException(404, "scan not found")
    db.delete(scan)  # cascades to CryptoAsset -> Finding via relationship config
    db.commit()
    return {"deleted": scan_id}


@app.delete("/scans")
def delete_all_scans(db: Session = Depends(get_db)):
    scans = db.query(models.ScanRun).all()
    count = len(scans)
    for scan in scans:
        db.delete(scan)  # per-object delete so ORM cascades to assets/findings correctly
    db.commit()
    return {"deleted_count": count}


# ---------------------------------------------------------------------------
# Settings / criticality / recommendations
# ---------------------------------------------------------------------------

@app.get("/settings/mosca-z")
def get_mosca_z(db: Session = Depends(get_db)):
    row = db.query(models.Settings).filter(models.Settings.key == "mosca_z").first()
    return {"z_years": float(row.value) if row else 10.0}


@app.put("/settings/mosca-z")
def set_mosca_z(payload: schemas.MoscaZUpdate, db: Session = Depends(get_db)):
    row = db.query(models.Settings).filter(models.Settings.key == "mosca_z").first()
    if row:
        row.value = str(payload.z_years)
    else:
        row = models.Settings(key="mosca_z", value=str(payload.z_years))
        db.add(row)
    db.commit()
    return {"z_years": payload.z_years}


@app.get("/settings/criticality-tags")
def list_criticality_tags():
    return CRITICALITY_DEFAULTS


@app.put("/assets/{asset_id}/criticality")
def update_asset_criticality(asset_id: int, payload: schemas.CriticalityUpdate, db: Session = Depends(get_db)):
    from app.risk.scorer import score_asset

    asset = db.query(models.CryptoAsset).filter(models.CryptoAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(404, "asset not found")
    if payload.criticality_tag not in CRITICALITY_DEFAULTS:
        raise HTTPException(400, "unknown criticality_tag")

    asset.criticality_tag = payload.criticality_tag
    z_row = db.query(models.Settings).filter(models.Settings.key == "mosca_z").first()
    global_z = float(z_row.value) if z_row else 10.0

    score = score_asset(asset.algorithm or "unknown", asset.criticality_tag, global_z)
    finding = asset.finding
    if finding:
        for k, v in score.items():
            setattr(finding, k, v)
    else:
        finding = models.Finding(asset_id=asset.id, **score)
        db.add(finding)
    db.commit()
    db.refresh(asset)
    return schemas.AssetOut.model_validate(asset)


@app.get("/recommendations/{finding_id}")
def get_recommendation_detail(finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(models.Finding).filter(models.Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(404, "finding not found")
    return get_recommendation(finding.asset.algorithm or "unknown", finding.risk_level)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@app.get("/scan/{scan_id}/cbom")
def download_cbom(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(models.ScanRun).filter(models.ScanRun.id == scan_id).first()
    if not scan:
        raise HTTPException(404, "scan not found")
    bom = generate_cbom_dict(db, scan_id)
    import json
    return Response(
        content=json.dumps(bom, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=ecdat_cbom_scan_{scan_id}.json"},
    )


@app.get("/scan/{scan_id}/report.pdf")
def download_pdf_report(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(models.ScanRun).filter(models.ScanRun.id == scan_id).first()
    if not scan:
        raise HTTPException(404, "scan not found")
    pdf_bytes = generate_pdf_report(db, scan_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=ecdat_report_scan_{scan_id}.pdf"},
    )
