import { useRef, useEffect, useCallback } from "react";

export function useActiveSocket() {
  const activeSocketRef = useRef(null);

  const closeActiveSocket = useCallback(() => {
    if (activeSocketRef.current) {
      activeSocketRef.current.close();
      activeSocketRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      closeActiveSocket();
    };
  }, [closeActiveSocket]);

  return [activeSocketRef, closeActiveSocket];
}
