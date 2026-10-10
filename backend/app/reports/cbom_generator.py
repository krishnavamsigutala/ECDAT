import json
import datetime
from sqlalchemy.orm import Session
from app import models


def generate_cbom_dict(db: Session, scan_run_id: int) -> dict:
    """Build a CycloneDX-1.6-shaped CBOM document for a scan run.

    We build the JSON structure directly (rather than depending on the exact
    dataclass surface of cyclonedx-python-lib, which shifts across versions)
    so the tool stays robust — the shape matches the CycloneDX 1.6
    cryptographic-asset spec used by the ECDAT problem statement.
    """
    scan = db.query(models.ScanRun).filter(models.ScanRun.id == scan_run_id).first()
    assets = db.query(models.CryptoAsset).filter(models.CryptoAsset.scan_run_id == scan_run_id).all()

    components = []
    for asset in assets:
        finding = asset.finding
        crypto_properties = {
            "assetType": "algorithm" if asset.asset_type == "algorithm" else asset.asset_type,
            "algorithmProperties": {
                "primitive": asset.category or "unknown",
                "parameterSetIdentifier": str(asset.key_size) if asset.key_size else None,
                "executionEnvironment": "software-plain-ram",
            },
        }
        component = {
            "type": "cryptographic-asset",
            "name": asset.algorithm or asset.name or "unknown",
            "bom-ref": f"asset-{asset.id}",
            "cryptoProperties": crypto_properties,
            "evidence": {
                "occurrences": [{
                    "location": asset.source_file or asset.name or "unknown",
                    "line": asset.line_number,
                }]
            },
        }
        if finding:
            component["properties"] = [
                {"name": "ecdat:riskLevel", "value": finding.risk_level},
                {"name": "ecdat:quantumVulnerable", "value": str(finding.quantum_vulnerable)},
                {"name": "ecdat:mosca", "value": json.dumps({
                    "x": finding.mosca_x, "y": finding.mosca_y, "z": finding.mosca_z,
                    "atRisk": finding.at_risk,
                })},
                {"name": "ecdat:recommendation", "value": finding.recommendation_summary or ""},
            ]
        components.append(component)

    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:ecdat-scan-{scan_run_id}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "tools": [{"vendor": "ECDAT", "name": "Enterprise Cryptographic Discovery & Analysis Tool", "version": "0.1.0"}],
            "component": {
                "type": "application",
                "name": scan.target_ref if scan else "unknown-target",
            },
        },
        "components": components,
    }
    return bom
