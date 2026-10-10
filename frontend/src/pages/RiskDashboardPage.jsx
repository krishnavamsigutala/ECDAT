import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { api } from "../lib/api";
import RiskBadge from "../components/RiskBadge";
import { useLastScan } from "../lib/ScanContext";

const RISK_LEVELS = ["Critical", "High", "Medium", "Low"];
const RISK_COLORS = { Critical: "#DC2626", High: "#EA580C", Medium: "#CA8A04", Low: "#16A34A" };
const CRITICALITY_TAGS = [
  "public_internet_facing", "internal_only", "stores_sensitive_data", "long_term_archival",
];

export default function RiskDashboardPage() {
  const { scanId } = useParams();
  const { setScanId } = useLastScan();
  const [data, setData] = useState(null);
  const [z, setZ] = useState(10);
  const [error, setError] = useState(null);

  useEffect(() => {
    setScanId(Number(scanId));
    load();
    api.getMoscaZ().then((r) => setZ(r.z_years)).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scanId]);

  function load() {
    setError(null);
    api.getScanResults(scanId, { page_size: 500 }).then(setData).catch((e) => setError(e.message));
  }

  async function onZChange(newZ) {
    setZ(newZ);
    await api.setMoscaZ(newZ);
  }

  async function recomputeAll() {
    if (!data) return;
    await Promise.all(
      data.results.map((r) => api.updateAssetCriticality(r.id, r.criticality_tag))
    );
    load();
  }

  const riskCounts = useMemo(() => {
    if (!data) return [];
    const counts = Object.fromEntries(RISK_LEVELS.map((l) => [l, 0]));
    data.results.forEach((r) => {
      const lvl = r.finding?.risk_level;
      if (lvl && counts[lvl] !== undefined) counts[lvl] += 1;
    });
    return RISK_LEVELS.map((l) => ({ level: l, count: counts[l] }));
  }, [data]);

  const heatmap = useMemo(() => {
    if (!data) return {};
    const grid = {};
    CRITICALITY_TAGS.forEach((tag) => {
      grid[tag] = Object.fromEntries(RISK_LEVELS.map((l) => [l, 0]));
    });
    data.results.forEach((r) => {
      const tag = r.criticality_tag;
      const lvl = r.finding?.risk_level;
      if (grid[tag] && lvl) grid[tag][lvl] += 1;
    });
    return grid;
  }, [data]);

  const timeline = useMemo(() => {
    if (!data) return [];
    return data.results
      .filter((r) => r.finding)
      .map((r) => ({
        name: `${r.algorithm}${r.source_file ? " · " + r.source_file.split("/").pop() : ""}`,
        total: r.finding.mosca_x + r.finding.mosca_y,
        atRisk: r.finding.at_risk,
        risk: r.finding.risk_level,
      }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 12);
  }, [data]);

  if (error) return <div className="text-critical text-sm">{error}</div>;
  if (!data) return <div className="text-slate text-sm">Loading risk dashboard…</div>;

  return (
    <div>
      <div className="mb-6">
        <h1 className="font-display text-3xl text-ink">Risk dashboard</h1>
        <p className="text-sm text-slate mt-1">Scan #{scanId} · quantum-risk view of the asset inventory</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <Card title="Findings by risk level" className="lg:col-span-2">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={riskCounts} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8ED" vertical={false} />
              <XAxis dataKey="level" tick={{ fontSize: 12, fill: "#5B6B79" }} axisLine={{ stroke: "#E2E8ED" }} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#5B6B79" }} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: "#F6F8FA" }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {riskCounts.map((entry) => (
                  <Cell key={entry.level} fill={RISK_COLORS[entry.level]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Quantum-arrival assumption (Z)">
          <div className="flex flex-col h-full justify-between">
            <div>
              <div className="text-4xl font-display text-ink">{z}<span className="text-lg text-slate ml-1">yrs</span></div>
              <p className="text-xs text-slate mt-1">
                Years until a cryptographically-relevant quantum computer is assumed to exist.
              </p>
            </div>
            <input
              type="range"
              min={5}
              max={30}
              step={1}
              value={z}
              onChange={(e) => onZChange(Number(e.target.value))}
              onMouseUp={recomputeAll}
              onTouchEnd={recomputeAll}
              className="w-full accent-teal mt-4"
            />
            <div className="flex justify-between text-[11px] text-slate/70 mt-1">
              <span>5</span><span>30</span>
            </div>
            <button
              onClick={recomputeAll}
              className="mt-3 text-xs font-medium text-teal hover:text-tealbright"
            >
              Recompute risk with this Z →
            </button>
          </div>
        </Card>
      </div>

      <Card title="Criticality × risk heatmap" className="mb-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate uppercase tracking-wide">
                <th className="py-2 pr-4 font-medium">Criticality tag</th>
                {RISK_LEVELS.map((l) => (
                  <th key={l} className="py-2 px-3 font-medium text-center">{l}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CRITICALITY_TAGS.map((tag) => (
                <tr key={tag} className="border-t border-line">
                  <td className="py-2 pr-4 text-ink capitalize">{tag.replaceAll("_", " ")}</td>
                  {RISK_LEVELS.map((l) => {
                    const count = heatmap[tag]?.[l] || 0;
                    const intensity = Math.min(count / 4, 1);
                    return (
                      <td key={l} className="py-2 px-3 text-center">
                        <div
                          className="mx-auto rounded-md text-xs font-medium py-2 px-2 min-w-[36px]"
                          style={{
                            backgroundColor: count ? `${RISK_COLORS[l]}${Math.round(20 + intensity * 40).toString(16)}` : "transparent",
                            color: count ? RISK_COLORS[l] : "#5B6B79",
                          }}
                        >
                          {count}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Mosca timeline — top assets by X+Y vs Z">
        <div className="space-y-3">
          {timeline.map((t) => (
            <div key={t.name} className="flex items-center gap-3">
              <div className="w-48 shrink-0 text-xs text-slate truncate" title={t.name}>{t.name}</div>
              <div className="flex-1 h-4 bg-line rounded-full relative overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${Math.min((t.total / (z * 1.6)) * 100, 100)}%`,
                    backgroundColor: RISK_COLORS[t.risk],
                  }}
                />
                <div
                  className="absolute top-0 bottom-0 w-[2px] bg-ink"
                  style={{ left: `${Math.min((z / (z * 1.6)) * 100, 100)}%` }}
                  title={`Z = ${z} years`}
                />
              </div>
              <div className="w-14 shrink-0 text-xs text-right">
                <RiskBadge level={t.risk} />
              </div>
            </div>
          ))}
          {timeline.length === 0 && (
            <p className="text-sm text-slate">No scored findings yet.</p>
          )}
          <p className="text-[11px] text-slate/70 pt-1">
            Bar length is X (data lifetime) + Y (migration time); the dark line marks the
            current Z assumption. Bars crossing the line are at risk under Mosca's theorem.
          </p>
        </div>
      </Card>
    </div>
  );
}

function Card({ title, children, className = "" }) {
  return (
    <div className={`bg-white border border-line rounded-lg p-5 ${className}`}>
      <h2 className="text-sm font-medium text-ink mb-4">{title}</h2>
      {children}
    </div>
  );
}
