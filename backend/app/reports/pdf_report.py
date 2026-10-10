import io
import datetime
from collections import Counter
from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from app import models

RISK_COLORS = {
    "Critical": colors.HexColor("#DC2626"),
    "High": colors.HexColor("#EA580C"),
    "Medium": colors.HexColor("#CA8A04"),
    "Low": colors.HexColor("#16A34A"),
}


def generate_pdf_report(db: Session, scan_run_id: int) -> bytes:
    scan = db.query(models.ScanRun).filter(models.ScanRun.id == scan_run_id).first()
    assets = db.query(models.CryptoAsset).filter(models.CryptoAsset.scan_run_id == scan_run_id).all()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ECDATTitle", parent=styles["Title"], textColor=colors.HexColor("#0B2545"))
    h2 = ParagraphStyle("ECDATH2", parent=styles["Heading2"], textColor=colors.HexColor("#0B2545"))
    body = styles["BodyText"]

    story = []
    story.append(Paragraph("Enterprise Cryptographic Discovery &amp; Analysis Tool", title_style))
    story.append(Paragraph("Cryptographic Risk Scan Report", styles["Heading3"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Target: {scan.target_ref if scan else 'N/A'} ({scan.target_type if scan else ''})", body))
    story.append(Paragraph(f"Scan date: {scan.created_at.strftime('%Y-%m-%d %H:%M UTC') if scan else datetime.datetime.utcnow().isoformat()}", body))
    story.append(Paragraph(f"Total crypto assets found: {len(assets)}", body))
    story.append(Spacer(1, 16))

    counts = Counter(a.finding.risk_level if a.finding else "Unscored" for a in assets)
    story.append(Paragraph("Executive Summary", h2))
    summary_data = [["Risk Level", "Count"]] + [[level, str(counts.get(level, 0))] for level in ("Critical", "High", "Medium", "Low")]
    summary_table = Table(summary_data, colWidths=[6 * cm, 4 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B2545")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Findings", h2))
    if not assets:
        story.append(Paragraph("No cryptographic assets were found in this scan.", body))
    else:
        table_data = [["Algorithm", "Location", "Risk", "Recommendation"]]
        for a in assets:
            loc = f"{a.source_file or a.name or '-'}" + (f":{a.line_number}" if a.line_number else "")
            risk = a.finding.risk_level if a.finding else "-"
            rec = (a.finding.recommendation_summary if a.finding else "-") or "-"
            table_data.append([
                Paragraph(a.algorithm or "-", body),
                Paragraph(loc, body),
                Paragraph(risk, body),
                Paragraph(rec[:180], body),
            ])
        findings_table = Table(table_data, colWidths=[3 * cm, 4 * cm, 2 * cm, 7 * cm], repeatRows=1)
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B2545")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        for i, a in enumerate(assets, start=1):
            level = a.finding.risk_level if a.finding else None
            if level in RISK_COLORS:
                style_cmds.append(("TEXTCOLOR", (2, i), (2, i), RISK_COLORS[level]))
        findings_table.setStyle(TableStyle(style_cmds))
        story.append(findings_table)

    story.append(PageBreak())
    story.append(Paragraph("Methodology", h2))
    story.append(Paragraph(
        "Risk is scored using Mosca's theorem: an asset is considered at risk when "
        "X (years the data must remain confidential) plus Y (years to migrate this "
        "system to post-quantum cryptography) exceeds Z (assumed years until a "
        "cryptographically-relevant quantum computer exists). X and Y are derived from "
        "each asset's business-criticality tag; Z is a configurable global assumption "
        f"(currently {scan.assets[0].finding.mosca_z if scan and scan.assets and scan.assets[0].finding else 'N/A'} years). "
        "Final risk level combines the Mosca outcome with quantum-vulnerability status "
        "(Shor's algorithm for asymmetric crypto, Grover's algorithm for symmetric/hash) "
        "and business criticality.",
        body,
    ))

    doc.build(story)
    return buf.getvalue()
