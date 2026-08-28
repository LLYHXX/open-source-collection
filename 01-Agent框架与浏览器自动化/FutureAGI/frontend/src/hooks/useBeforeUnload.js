import { useEffect } from "react";

/**
 * Prevents page navigation/reload when condition is true
 * (except during vite:preloadError recovery)
 *
 * @param {boolean} shouldPrevent - When true, shows browser confirmation before leaving
 * @param {string} [message] - Optional custom message (note: most browsers ignore custom messages)
 */
export function useBeforeUnload(shouldPrevent, message = "") {
  useEffect(() => {
    const handleBeforeUnload = (event) => {
      // Allow vite:preloadError recovery reload to proceed without confirmation
      if (window.__RELOADING_FOR_VITE_PRELOAD_ERROR) return;

      event.preventDefault();
      event.returnValue = message || ""; // Required for modern browsers
    };

    if (shouldPrevent) {
      window.addEventListener("beforeunload", handleBeforeUnload);
    } else {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    }

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [shouldPrevent, message]);
}
