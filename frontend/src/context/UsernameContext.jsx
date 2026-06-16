import { createContext, useCallback, useContext, useMemo, useState } from "react";

const STORAGE_KEY = "morphy_username";

function normalizeUsername(raw) {
  return raw.trim().toLowerCase().replace(/[^a-z0-9_-]/g, "");
}

const UsernameContext = createContext(null);

export function UsernameProvider({ children }) {
  const [username, setUsernameState] = useState(
    () => localStorage.getItem(STORAGE_KEY) ?? "",
  );

  const setUsername = useCallback((next) => {
    const normalized = normalizeUsername(next);
    setUsernameState(normalized);
    if (normalized) {
      localStorage.setItem(STORAGE_KEY, normalized);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
    return normalized;
  }, []);

  const clearUsername = useCallback(() => {
    setUsername("");
  }, [setUsername]);

  const value = useMemo(
    () => ({ username, setUsername, clearUsername, normalizeUsername }),
    [username, setUsername, clearUsername],
  );

  return (
    <UsernameContext.Provider value={value}>{children}</UsernameContext.Provider>
  );
}

export function useUsername() {
  const ctx = useContext(UsernameContext);
  if (!ctx) throw new Error("useUsername must be used within UsernameProvider");
  return ctx;
}
