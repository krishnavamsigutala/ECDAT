import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import RiskBadge from "../components/RiskBadge";
import RecommendationPanel from "../components/RecommendationPanel";
import { useLastScan } from "../lib/ScanContext";

const RISK_LEVELS = ["Critical", "High", "Medium", "Low"];
const CRITICALITY_TAGS = [
  "public_internet_facing",
  "internal_only",
  "stores_sensitive_data",
  "long_term_archival",
];

export default function InventoryPage() {
  const { scanId } = useParams();
  const { setScanId } = useLastScan();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [riskFilter, setRiskFilter] = useState("");
  const [languageFilter, setLanguageFilter] = useState("");
  const [search, setSearch] = useState("");
  const [openAsset, setOpenAsset] = useState(null);

  useEffect(() => {
    setScanId(Number(scanId));
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scanId, riskFilter, languageFilter]);

  function load() {
    setError(null);
    api
      .getScanResults(scanId, { risk_level: riskFilter, language: languageFilter, page_size: 500 })
      .then(setData)
      .catch((e) => setError(e.message));
  }

  const languages = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.results.map((r) => r.language).filter(Boolean))];
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    if (!search.trim()) return data.results;
    const q = search.toLowerCase();
    return data.results.filter(
      (r) =>
        (r.algorithm || "").toLowerCase().includes(q) ||
        (r.source_file || "").toLowerCase().includes(q) ||
        (r.name || "").toLowerCase().includes(q)
    );
  }, [data, search]);

  async function changeCriticality(assetId, tag) {
    await api.updateAssetCriticality(assetId, tag);
    load();
  }

  if (error) return <div className="text-critical text-sm">{error}</div>;
  if (!data) return <div className="text-slate text-sm">Loading inventory…</div>;

  return (
    <div>
      <div className="flex items-baseline justify-between mb-6">
        <div>
          <h1 className="font-display text-3xl text-ink">Asset inventory</h1>
          <p className="text-sm text-slate mt-1">
            Scan #{scanId} · {data.total} cryptographic asset{data.total === 1 ? "" : "s"} found
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search algorithm or file…"
          className="rounded-md border border-line px-3 py-2 text-sm flex-1 min-w-[220px] focus:outline-none focus:ring-2 focus:ring-teal/40"
        />
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          className="rounded-md border border-line px-3 py-2 text-sm bg-white"
        >
          <option value="">All risk levels</option>
          {RISK_LEVELS.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
        <select
          value={languageFilter}
          onChange={(e) => setLanguageFilter(e.target.value)}
          className="rounded-md border border-line px-3 py-2 text-sm bg-white"
        >
          <option value="">All languages</option>
          {languages.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
      </div>

      <p className="text-xs text-slate mb-2">
        <span className="font-mono">Mosca X/Y/Z</span> = data lifetime / migration time / assumed years
        until a quantum computer exists. Red = X+Y exceeds Z (at risk now). "Suggested fix" appears
        for anything above Low risk.
      </p>

      <div className="bg-white border border-line rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-paper text-left text-xs text-slate uppercase tracking-wide">
              <th className="px-4 py-3 font-medium">Algorithm</th>
              <th className="px-4 py-3 font-medium">Category</th>
              <th className="px-4 py-3 font-medium">Location</th>
              <th className="px-4 py-3 font-medium">Key size</th>
              <th className="px-4 py-3 font-medium">Criticality</th>
              <th className="px-4 py-3 font-medium">Mosca X/Y/Z</th>
              <th className="px-4 py-3 font-medium">Risk</th>
              <th className="px-4 py-3 font-medium">Suggested fix</th>
              <th className="px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={row.id} className="border-t border-line hover:bg-paper/60">
                <td className="px-4 py-3 font-mono text-ink">{row.algorithm}{row.mode ? `/${row.mode}` : ""}</td>
                <td className="px-4 py-3 text-slate capitalize">{row.category}</td>
                <td className="px-4 py-3 text-slate">
                  {row.source_file}
                  {row.line_number ? <span className="text-slate/60">:{row.line_number}</span> : null}
                </td>
                <td className="px-4 py-3 text-slate">{row.key_size || "—"}</td>
                <td className="px-4 py-3">
                  <select
                    value={row.criticality_tag}
                    onChange={(e) => changeCriticality(row.id, e.target.value)}
                    className="text-xs border border-line rounded-md px-2 py-1 bg-white"
                  >
                    {CRITICALITY_TAGS.map((tag) => (
                      <option key={tag} value={tag}>{tag.replaceAll("_", " ")}</option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3">
                  {row.finding ? (
                    <div
                      className={`inline-flex items-center gap-1.5 text-xs font-mono rounded-md px-2 py-1 ${
                        row.finding.at_risk ? "bg-critical/10 text-critical" : "bg-low/10 text-low"
                      }`}
                      title={`X=${row.finding.mosca_x}y (data lifetime), Y=${row.finding.mosca_y}y (migration time), Z=${row.finding.mosca_z}y (quantum arrival)`}
                    >
                      <span>{row.finding.mosca_x}</span>
                      <span className="opacity-50">/</span>
                      <span>{row.finding.mosca_y}</span>
                      <span className="opacity-50">/</span>
                      <span>{row.finding.mosca_z}</span>
                    </div>
                  ) : (
                    <span className="text-slate/50">—</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <RiskBadge level={row.finding?.risk_level} />
                </td>
                <td className="px-4 py-3 max-w-xs">
                  {row.finding && row.finding.risk_level !== "Low" ? (
                    <span className="text-xs text-ink">
                      → {row.finding.recommendation_summary}
                    </span>
                  ) : row.finding ? (
                    <span className="text-xs text-slate/50">No action needed</span>
                  ) : (
                    <span className="text-slate/50">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right">
                  {row.finding && (
                    <button
                      onClick={() => setOpenAsset(row)}
                      className="text-xs text-teal hover:text-tealbright font-medium"
                    >
                      Why this? →
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-10 text-center text-slate text-sm">
                  No assets match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <RecommendationPanel
        finding={openAsset?.finding}
        algorithm={openAsset?.algorithm}
        onClose={() => setOpenAsset(null)}
      />
    </div>
  );
}
