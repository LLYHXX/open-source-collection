import { useState, useEffect } from "react";

const MEDIA_QUERY = "(prefers-color-scheme: dark)";

function getSystemMode() {
  if (typeof window === "undefined") return "light";
  return window.matchMedia(MEDIA_QUERY).matches ? "dark" : "light";
}

/**
 * Returns "light" or "dark" based on the OS color-scheme preference.
 * Re-renders automatically when the user toggles their OS theme.
 */
export function useSystemThemeMode() {
  const [mode, setMode] = useState(getSystemMode);

  useEffect(() => {
    const mql = window.matchMedia(MEDIA_QUERY);
    const handler = (e) => setMode(e.matches ? "dark" : "light");
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  return mode;
}
