import { createContext, useContext, useState, useCallback } from "react";

const STORAGE_KEY = "ecdat_last_scan_id";
const ScanContext = createContext(null);

export function ScanProvider({ children }) {
  const [scanId, setScanIdState] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? Number(stored) : null;
  });

  const setScanId = useCallback((id) => {
    setScanIdState(id);
    if (id) {
      localStorage.setItem(STORAGE_KEY, String(id));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  return (
    <ScanContext.Provider value={{ scanId, setScanId }}>
      {children}
    </ScanContext.Provider>
  );
}

export function useLastScan() {
  const ctx = useContext(ScanContext);
  if (!ctx) throw new Error("useLastScan must be used within a ScanProvider");
  return ctx;
}
