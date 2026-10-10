import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useLastScan } from "../lib/ScanContext";

const TARGET_TYPES = [
  { value: "repo", label: "Git repo URL", placeholder: "https://github.com/org/project.git" },
  { value: "local", label: "Local path (server-side)", placeholder: "test_fixtures" },
  { value: "image", label: "Container image", placeholder: "myregistry/app:latest" },
  { value: "zip", label: "Upload ZIP archive", placeholder: null },
  { value: "binary", label: "Upload binary", placeholder: null },
];

export default function ScanPage() {
  const [targetType, setTargetType] = useState("repo");
  const [targetRef, setTargetRef] = useState("");
  const [file, setFile] = useState(null);
  const [scan, setScan] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const pollRef = useRef(null);
  const navigate = useNavigate();
  const { setScanId } = useLastScan();

  const activeMeta = TARGET_TYPES.find((t) => t.value === targetType);
  const isUpload = targetType === "zip" || targetType === "binary";

  useEffect(() => () => clearInterval(pollRef.current), []);

  async function startScan(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      let created;
      if (isUpload) {
        if (!file) throw new Error("Choose a file to upload first.");
        created = await api.createScanUpload(targetType, file);
      } else {
        if (!targetRef.trim()) throw new Error("Enter a target before starting a scan.");
        created = await api.createScan(targetType, targetRef.trim());
      }
      setScan(created);
      setScanId(created.id);
      pollRef.current = setInterval(async () => {
        try {
          const s = await api.getScanStatus(created.id);
          setScan(s);
          if (s.status === "completed" || s.status === "failed") {
            clearInterval(pollRef.current);
          }
        } catch (err) {
          clearInterval(pollRef.current);
          setError(err.message);
        }
      }, 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="font-display text-3xl text-ink mb-1">Run a scan</h1>
      <p className="text-slate mb-8 text-sm">
        Point ECDAT at a source repository, an uploaded archive, a container image, or a
        local path, and it will inventory every cryptographic artefact it finds.
      </p>

      <form onSubmit={startScan} className="space-y-5 bg-white border border-line rounded-lg p-6">
        <div>
          <label className="block text-xs font-medium text-slate mb-2">Target type</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {TARGET_TYPES.map((t) => (
              <button
                type="button"
                key={t.value}
                onClick={() => {
                  setTargetType(t.value);
                  setTargetRef("");
                  setFile(null);
                }}
                className={`text-left px-3 py-2 rounded-md border text-sm transition-colors ${
                  targetType === t.value
                    ? "border-teal bg-teal/5 text-ink"
                    : "border-line text-slate hover:border-teal/40"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {isUpload ? (
          <div>
            <label className="block text-xs font-medium text-slate mb-2">File</label>
            <input
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-slate file:mr-3 file:py-2 file:px-3 file:rounded-md file:border-0 file:bg-teal file:text-white file:text-sm hover:file:bg-tealbright"
            />
          </div>
        ) : (
          <div>
            <label className="block text-xs font-medium text-slate mb-2">{activeMeta.label}</label>
            <input
              type="text"
              value={targetRef}
              onChange={(e) => setTargetRef(e.target.value)}
              placeholder={activeMeta.placeholder}
              className="w-full rounded-md border border-line px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-teal/40 focus:border-teal"
            />
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || (scan && !["completed", "failed"].includes(scan.status))}
          className="w-full rounded-md bg-ink text-white text-sm font-medium py-2.5 hover:bg-teal transition-colors disabled:opacity-50"
        >
          {submitting ? "Starting…" : "Start scan"}
        </button>
      </form>

      {error && (
        <div className="mt-4 rounded-md border border-critical/30 bg-critical/5 text-critical text-sm px-4 py-3">
          {error}
        </div>
      )}

      {scan && (
        <div className="mt-6 bg-white border border-line rounded-lg p-6">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm text-slate">Scan #{scan.id}</div>
            <StatusPill status={scan.status} />
          </div>
          <p className="text-sm text-ink mb-2">{scan.progress_message}</p>
          {scan.status !== "completed" && scan.status !== "failed" && (
            <div className="h-1.5 w-full bg-line rounded-full overflow-hidden">
              <div className="h-full bg-teal animate-pulse w-2/3" />
            </div>
          )}
          {scan.status === "failed" && scan.error_message && (
            <pre className="mt-3 text-xs text-critical bg-critical/5 rounded-md p-3 overflow-auto max-h-40 whitespace-pre-wrap">
              {scan.error_message}
            </pre>
          )}
          {scan.status === "completed" && (
            <div className="mt-4 flex gap-3">
              <button
                onClick={() => navigate(`/risk/${scan.id}`)}
                className="rounded-md bg-teal text-white text-sm font-medium px-4 py-2 hover:bg-tealbright"
              >
                View risk dashboard
              </button>
              <button
                onClick={() => navigate(`/inventory/${scan.id}`)}
                className="rounded-md border border-line text-ink text-sm font-medium px-4 py-2 hover:border-teal"
              >
                Browse inventory
              </button>
            </div>
          )}
        </div>
      )}
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
    <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${map[status] || map.pending}`}>
      {status}
    </span>
  );
}
