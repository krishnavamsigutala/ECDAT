import { Routes, Route, useLocation, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import ScanPage from "./pages/ScanPage";
import InventoryPage from "./pages/InventoryPage";
import RiskDashboardPage from "./pages/RiskDashboardPage";
import ScanHistoryPage from "./pages/ScanHistoryPage";
import { api } from "./lib/api";
import { ScanProvider } from "./lib/ScanContext";

export default function App() {
  return (
    <ScanProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <TopBar />
          <main className="flex-1 px-8 py-8">
            <Routes>
              <Route path="/" element={<ScanPage />} />
              <Route path="/inventory/:scanId" element={<InventoryPage />} />
              <Route path="/risk/:scanId" element={<RiskDashboardPage />} />
              <Route path="/history" element={<ScanHistoryPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </ScanProvider>
  );
}

function TopBar() {
  const location = useLocation();
  const [backendOk, setBackendOk] = useState(null);

  useEffect(() => {
    api.health().then(() => setBackendOk(true)).catch(() => setBackendOk(false));
    const interval = setInterval(() => {
      api.health().then(() => setBackendOk(true)).catch(() => setBackendOk(false));
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  const titleMap = {
    "/": "Scan",
    "/history": "Scan History",
  };
  const title =
    titleMap[location.pathname] ||
    (location.pathname.startsWith("/inventory") ? "Asset Inventory" :
     location.pathname.startsWith("/risk") ? "Risk Dashboard" : "ECDAT");

  return (
    <header className="h-14 border-b border-line bg-white flex items-center justify-between px-8">
      <span className="text-sm font-medium text-ink">{title}</span>
      <span className="flex items-center gap-2 text-xs text-slate">
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            backendOk === null ? "bg-slate/40" : backendOk ? "bg-low" : "bg-critical"
          }`}
        />
        {backendOk === null ? "Checking backend…" : backendOk ? "Backend connected" : "Backend unreachable"}
      </span>
    </header>
  );
}
