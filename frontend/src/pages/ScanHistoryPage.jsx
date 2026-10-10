import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import RiskBadge from "../components/RiskBadge";
import { useLastScan } from "../lib/ScanContext";

export default function ScanHistoryPage() {
  const [scans, setScans] = useState(null);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [confirmClearAll, setConfirmClearAll] = useState(false);
  const navigate = useNavigate();
  const { scanId: lastScanId, setScanId } = useLastScan();

  useEffect(() => {
    load();
  }, []);

  function load() {
    api.listScans().then(setScans).catch((e) => setError(e.message));
  }

  async function handleDelete(id, e) {
    e.stopPropagation();
    if (!window.confirm(`Delete scan #${id}? This removes all its findings and can't be undone.`)) {
      return;
    }
    setDeletingId(id);
    try {
      await api.deleteScan(id);
      if (lastScanId === id) setScanId(null);
      load();
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
    }
  }

  async function handleClearAll() {
    if (!confirmClearAll) {
      setConfirmClearAll(true);
      return;
    }
    try {
      await api.deleteAllScans();
      setScanId(null);
      setConfirmClearAll(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  if (error) return <div className="text-critical text-sm">{error}</div>;
  if (!scans) return <div className="text-slate text-sm">Loading scan history…</div>;

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="font-display text-3xl text-ink mb-1">Scan history</h1>
          <p className="text-sm text-slate">{scans.length} scan{scans.length === 1 ? "" : "s"} on record</p>
        </div>
        {scans.length > 0 && (
          <button
            onClick={handleClearAll}
            onBlur={() => setConfirmClearAll(false)}
            className={`text-xs font-medium rounded-md px-3 py-2 border transition-colors ${
              confirmClearAll
                ? "bg-critical text-white border-critical"
                : "text-critical border-critical/30 hover:bg-critical/5"
            }`}
          >
            {confirmClearAll ? "Click again to confirm — deletes everything" : "Clear all history"}
          </button>
        )}
      </div>

      {scans.length === 0 && (
        <div className="bg-white border border-line rounded-lg p-10 text-center text-slate text-sm">
          No scans yet — head to the Scan page to run your first one.
        </div>
      )}

      <div className="space-y-3">
        {scans.map((s) => (
          <div key={s.id} className="bg-white border border-line rounded-lg p-4 flex items-center justify-between gap-4">
            <div
              className="flex-1 min-w-0 cursor-pointer"
              onClick={() => {
                if (s.status !== "completed") return;
                setScanId(s.id);
                navigate(`/risk/${s.id}`);
              }}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-slate">#{s.id}</span>
                <span className="text-xs uppercase tracking-wide text-slate/70">{s.target_type}</span>
                <StatusPill status={s.status} />
              </div>
              <div className="text-sm text-ink truncate font-mono">{s.target_ref}</div>
              <div className="text-xs text-slate mt-1">
                {new Date(s.created_at).toLocaleString()} · {s.total_assets} assets
              </div>
            </div>

            <div className="hidden sm:flex items-center gap-1.5">
              {["Critical", "High", "Medium", "Low"].map((lvl) =>
                s.counts[lvl] ? (
                  <div key={lvl} className="flex items-center gap-1">
                    <RiskBadge level={lvl} />
                    <span className="text-xs text-slate">×{s.counts[lvl]}</span>
                  </div>
                ) : null
              )}
            </div>

            {s.status === "completed" && (
              <div className="flex gap-2 shrink-0">
                <a
                  href={api.cbomUrl(s.id)}
                  onClick={(e) => e.stopPropagation()}
                  className="text-xs font-medium text-teal hover:text-tealbright border border-teal/30 rounded-md px-3 py-1.5"
                >
                  CBOM
                </a>
                <a
                  href={api.pdfReportUrl(s.id)}
                  onClick={(e) => e.stopPropagation()}
                  className="text-xs font-medium text-teal hover:text-tealbright border border-teal/30 rounded-md px-3 py-1.5"
                >
                  PDF report
                </a>
              </div>
            )}

            <button
              onClick={(e) => handleDelete(s.id, e)}
              disabled={deletingId === s.id}
              title="Delete this scan"
              className="shrink-0 text-slate hover:text-critical text-sm px-2 py-1.5 rounded-md hover:bg-critical/5 disabled:opacity-40"
            >
              {deletingId === s.id ? "…" : "✕"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusPill({ status }) {
  const map = {
    pending: "bg-slate/10 text-slate",
    running: "bg-teal/10 text-teal",
    completed: "bg-low/10 text-low",
    failed: "bg-critical/10 text-critical",
  };
  return (
    <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${map[status] || map.pending}`}>
      {status}
    </span>
  );
}
