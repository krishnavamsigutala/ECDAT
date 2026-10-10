const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch (_) {
      /* ignore */
    }
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json();
}

export const api = {
  base: API_BASE,

  health: () => fetch(`${API_BASE}/health`).then(handle),

  createScan: (target_type, target_ref) =>
    fetch(`${API_BASE}/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_type, target_ref }),
    }).then(handle),

  createScanUpload: (target_type, file) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${API_BASE}/scan/upload?target_type=${target_type}`, {
      method: "POST",
      body: form,
    }).then(handle);
  },

  getScanStatus: (id) => fetch(`${API_BASE}/scan/${id}/status`).then(handle),

  getScanResults: (id, params = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== ""))
    ).toString();
    return fetch(`${API_BASE}/scan/${id}/results${qs ? `?${qs}` : ""}`).then(handle);
  },

  listScans: () => fetch(`${API_BASE}/scans`).then(handle),
  deleteScan: (id) => fetch(`${API_BASE}/scan/${id}`, { method: "DELETE" }).then(handle),
  deleteAllScans: () => fetch(`${API_BASE}/scans`, { method: "DELETE" }).then(handle),

  getMoscaZ: () => fetch(`${API_BASE}/settings/mosca-z`).then(handle),
  setMoscaZ: (z_years) =>
    fetch(`${API_BASE}/settings/mosca-z`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ z_years }),
    }).then(handle),

  listCriticalityTags: () => fetch(`${API_BASE}/settings/criticality-tags`).then(handle),
  updateAssetCriticality: (assetId, criticality_tag) =>
    fetch(`${API_BASE}/assets/${assetId}/criticality`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ criticality_tag }),
    }).then(handle),

  getRecommendation: (findingId) =>
    fetch(`${API_BASE}/recommendations/${findingId}`).then(handle),

  cbomUrl: (scanId) => `${API_BASE}/scan/${scanId}/cbom`,
  pdfReportUrl: (scanId) => `${API_BASE}/scan/${scanId}/report.pdf`,
};
