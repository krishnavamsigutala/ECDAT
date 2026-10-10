const STYLES = {
  Critical: "bg-critical/10 text-critical border-critical/30",
  High: "bg-high/10 text-high border-high/30",
  Medium: "bg-medium/10 text-medium border-medium/30",
  Low: "bg-low/10 text-low border-low/30",
};

export default function RiskBadge({ level, size = "sm" }) {
  const cls = STYLES[level] || "bg-slate/10 text-slate border-slate/30";
  const pad = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";
  return (
    <span className={`inline-flex items-center rounded-full border font-medium ${pad} ${cls}`}>
      {level || "Unscored"}
    </span>
  );
}
