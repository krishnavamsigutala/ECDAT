import { useEffect, useState } from "react";
import { api } from "../lib/api";
import RiskBadge from "./RiskBadge";

export default function RecommendationPanel({ finding, algorithm, onClose }) {
  const [rec, setRec] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!finding) return;
    setRec(null);
    setError(null);
    api.getRecommendation(finding.id).then(setRec).catch((e) => setError(e.message));
  }, [finding]);

  if (!finding) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div className="absolute inset-0 bg-ink/30" onClick={onClose} />
      <div className="relative w-full max-w-md h-full bg-white border-l border-line shadow-xl p-6 overflow-y-auto">
        <div className="flex items-start justify-between mb-4">
          <h2 className="font-display text-xl text-ink">Recommendation</h2>
          <button onClick={onClose} className="text-slate hover:text-ink text-sm">✕</button>
        </div>

        {error && <div className="text-sm text-critical">{error}</div>}

        <div className="space-y-5">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm text-ink">{algorithm}</span>
            <RiskBadge level={finding.risk_level} />
          </div>

          <Field label="Mosca's theorem inputs">
            <div className="grid grid-cols-3 gap-2">
              <MoscaStat label="X (data lifetime)" value={`${finding.mosca_x}y`} />
              <MoscaStat label="Y (migration time)" value={`${finding.mosca_y}y`} />
              <MoscaStat label="Z (quantum arrival)" value={`${finding.mosca_z}y`} />
            </div>
            <div className={`mt-2 text-xs font-medium rounded-md px-2.5 py-1.5 inline-block ${
              finding.at_risk ? "bg-critical/10 text-critical" : "bg-low/10 text-low"
            }`}>
              X + Y = {finding.mosca_x + finding.mosca_y}y
              {finding.at_risk ? " > " : " ≤ "}
              Z = {finding.mosca_z}y → {finding.at_risk ? "at risk now" : "not yet at risk"}
            </div>
          </Field>

          <Field label="Why this risk level">
            <p className="text-sm text-slate leading-relaxed">{finding.explanation}</p>
          </Field>

          {rec && (
            <>
              <Field label="Recommended path">
                <span className="text-sm font-medium text-ink capitalize">{rec.recommended_form}</span>
              </Field>

              <Field label="What to do">
                <p className="text-sm text-ink leading-relaxed">{rec.recommendation}</p>
              </Field>

              <div className="grid grid-cols-1 gap-3 pt-2 border-t border-line">
                <MiniStat label="Latency impact" value={rec.latency_impact} />
                <MiniStat label="Size impact" value={rec.size_impact} />
                <MiniStat label="Library maturity" value={rec.library_maturity} />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-slate/70 mb-1">{label}</div>
      {children}
    </div>
  );
}

function MoscaStat({ label, value }) {
  return (
    <div className="bg-paper rounded-md px-2 py-2 text-center">
      <div className="text-base font-display text-ink">{value}</div>
      <div className="text-[10px] text-slate/70 leading-tight mt-0.5">{label}</div>
    </div>
  );
}

function MiniStat({ label, value }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate">{label}</span>
      <span className="text-ink font-medium capitalize">{value}</span>
    </div>
  );
}
