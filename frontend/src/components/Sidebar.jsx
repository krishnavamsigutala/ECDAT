import { NavLink } from "react-router-dom";
import { useLastScan } from "../lib/ScanContext";

export default function Sidebar() {
  const { scanId } = useLastScan();
  const inventoryTo = scanId ? `/inventory/${scanId}` : "/history";
  const riskTo = scanId ? `/risk/${scanId}` : "/history";

  return (
    <aside className="w-60 shrink-0 bg-ink text-white flex flex-col min-h-screen">
      <div className="px-6 py-6 border-b border-white/10">
        <div className="font-display text-xl leading-tight">ECDAT</div>
        <div className="text-[11px] text-white/50 mt-1 leading-snug">
          Enterprise Cryptographic Discovery &amp; Analysis
        </div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        <NavItem to="/" label="Scan" />
        <NavItem to={inventoryTo} label="Asset Inventory" />
        <NavItem to={riskTo} label="Risk Dashboard" />
        <NavItem to="/history" label="Scan History" />
      </nav>
      <div className="px-6 py-4 border-t border-white/10 text-[11px] text-white/40 leading-snug">
        SIH 2026 · PS 26164 · NTRO
        <br />
        Blockchain &amp; Cybersecurity
      </div>
    </aside>
  );
}

function NavItem({ to, label }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
        `block rounded-md px-3 py-2 text-sm transition-colors ${
          isActive
            ? "bg-teal text-white"
            : "text-white/70 hover:bg-white/5 hover:text-white"
        }`
      }
    >
      {label}
    </NavLink>
  );
}
