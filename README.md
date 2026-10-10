# ECDAT — Enterprise Cryptographic Discovery & Analysis Tool

Built for Smart India Hackathon, **Problem Statement 26164** (National Technical
Research Organisation) — *Blockchain & Cybersecurity*, Software category.

## The problem, in one paragraph

Quantum computers will eventually break RSA, ECC, and Diffie-Hellman via Shor's
algorithm. Attackers can already harvest encrypted data today and decrypt it once
a quantum computer exists ("harvest now, decrypt later"). Before any organisation
can migrate to post-quantum cryptography (PQC), it first needs to know what
cryptography it's already using — and that's usually scattered across source
code, certs, TLS configs, third-party libraries, and container images. ECDAT
scans all of that, classifies each cryptographic asset's quantum risk using
**Mosca's theorem**, recommends a concrete **PQC/hybrid replacement**, and
exports a standards-compliant **CycloneDX CBOM** plus a PDF report.

## Architecture

```
GitHub/Repo, Uploaded ZIP, Container Image, Cert/Key files
                    │
        1. INGESTION LAYER (clone / unzip / pull image)
                    │
        2. CRYPTO DETECTION ENGINE
           (Python/Java/C/C++/JS/Go source, certs, TLS configs,
            binary strings, container SBOM via Syft)
                    │
        3. NORMALIZATION (unified crypto-asset schema)
                    │
        4. RISK CLASSIFICATION ENGINE
           (quantum-vulnerability lookup + Mosca's theorem
            X+Y>Z + business-criticality weighting)
                    │
        5. PQC RECOMMENDATION ENGINE
           (ML-KEM / ML-DSA / SLH-DSA / hybrid mappings)
                    │
        6a. CBOM GENERATOR (CycloneDX JSON)   6b. PDF REPORT GENERATOR
                    │
        7. PERSISTENCE (SQLite/Postgres via SQLAlchemy)
                    │
        8. REST API (FastAPI: /scan, /results, /cbom, /report)
                    │
        9. REACT DASHBOARD (inventory, risk heatmap, Mosca timeline,
           recommendation panel, CBOM/PDF export, scan history)
```

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + TailwindCSS + Recharts |
| Backend API | Python + FastAPI |
| Detection engine | Python `re`/`ast` + YAML rule files |
| Binary / container scan | `strings` + Anchore Syft |
| Cert/key inspection | Python `cryptography` library |
| Database | SQLite (dev), swappable to PostgreSQL via `DATABASE_URL` |
| CBOM export | Hand-built CycloneDX 1.6 JSON (`cryptographic-asset` components) |
| Report export | ReportLab (PDF) |
| Packaging | Docker + docker-compose |

## Setup

### Option A — one command (Docker)

```bash
docker compose up --build
```

This builds and starts the backend (`:8000`), seeds it with three demo
projects (mixed weak/strong crypto) so the dashboard has data immediately,
and starts the frontend (`:5173`). Open **http://localhost:5173**.

### Option B — run locally without Docker

```bash
# backend
cd backend
pip install -r requirements.txt --break-system-packages   # or use a venv
uvicorn app.main:app --reload --port 8000

# frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173. The frontend expects the API at
`http://localhost:8000` (see `frontend/.env`, `VITE_API_BASE`).

### Try it immediately against the bundled fixtures

```bash
curl -X POST http://localhost:8000/scan/local \
  -H "Content-Type: application/json" \
  -d '{"target_type":"local","target_ref":"test_fixtures"}'
```

Poll `GET /scan/{id}/status` until `"status":"completed"`, then open the
returned scan in the dashboard (`/risk/{id}` or `/inventory/{id}`), or fetch
`GET /scan/{id}/cbom` / `GET /scan/{id}/report.pdf` directly.

## API surface

| Method | Path | Purpose |
|---|---|---|
| POST | `/scan` | Start a scan (`{target_type, target_ref}`; repo / zip / image / binary / local) |
| POST | `/scan/upload?target_type=zip\|binary` | Start a scan from an uploaded file |
| POST | `/scan/local` | Convenience: scan a server-local path (used by the seed script and test fixtures) |
| GET | `/scan/{id}/status` | Poll scan progress |
| GET | `/scan/{id}/results` | Paginated findings, filterable by `risk_level`, `category`, `language` |
| GET | `/scans` | Scan history with per-risk-level counts |
| GET | `/settings/mosca-z` / PUT | Read/adjust the global Z (quantum-arrival) assumption |
| GET | `/settings/criticality-tags` | List available business-criticality tags and their default X/Y |
| PUT | `/assets/{id}/criticality` | Re-tag an asset and recompute its risk live |
| GET | `/recommendations/{finding_id}` | Full PQC/hybrid recommendation detail |
| GET | `/scan/{id}/cbom` | Download CycloneDX 1.6 CBOM JSON |
| GET | `/scan/{id}/report.pdf` | Download the PDF summary report |

Interactive Swagger docs are always available at `http://localhost:8000/docs`.

## 3-minute demo script

1. **Open on the risk dashboard**, not the scan form — the seeded demo scans
   already show a risk heatmap and Mosca timeline.
2. **Trigger a live scan** against a small real public GitHub repo (Scan page
   → Git repo URL) to prove it isn't canned data.
3. **Drag the Z slider** on the risk dashboard and watch risk levels
   recompute — this is the most memorable demo beat.
4. **Click a Critical finding** in the inventory table → "Why this?" to show
   the PQC recommendation panel (hybrid suggestion, latency/size notes,
   rationale).
5. **Download the CBOM JSON and PDF report** from the Scan History page to
   show a standards-shaped, enterprise-feeling deliverable.

## Project layout

```
ecdat/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app & all REST endpoints
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── orchestrator.py    # ingestion -> detection -> scoring pipeline
│   │   ├── detectors/         # per-language + cert/config/binary/container scanners
│   │   └── risk/              # Mosca calculator, criticality tags, scorer, PQC mappings
│   ├── reports/                # CBOM + PDF generators
│   ├── test_fixtures/          # sample files with obvious crypto usage, for quick testing
│   ├── demo/                   # 3 seeded demo projects (weak Python/Java + strong contrast)
│   └── scripts/seed_demo.py
├── frontend/
│   └── src/
│       ├── pages/               # Scan, Inventory, Risk Dashboard, Scan History
│       └── components/          # Sidebar, RiskBadge, RecommendationPanel
└── docker-compose.yml
```

## Talking to "how would this work in production?"

Not built, but straightforward to speak to: swap `BackgroundTasks` for a
Celery/Redis queue for concurrent scans, move SQLite → PostgreSQL (already a
one-line `DATABASE_URL` change), add RBAC in front of the FastAPI app, and
add cloud KMS/HSM connectors alongside the existing repo/zip/image/binary
ingestion paths.
