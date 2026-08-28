import { useEffect, useRef, useCallback } from "react";
import { useAuthContext } from "src/auth/hooks";
import { HOST_API } from "src/config-global";
import logger from "src/utils/logger";

/**
 * Opens a dedicated WebSocket to `ws/simulation-updates/` for the given
 * testId and invokes `onUpdate` whenever a `simulation_update` message
 * arrives.  Auto-reconnects on close with exponential back-off.
 *
 * Usage:
 *   useSimulationSocket(testId, () => refreshGrid());
 */
export const useSimulationSocket = (testId, onUpdate) => {
  const { user } = useAuthContext();
  const socketRef = useRef(null);
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;
  const retriesRef = useRef(0);
  const timerRef = useRef(null);
  // Track whether the hook is still mounted
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    const token = user?.accessToken;
    if (!token || !testId) return;

    // Don't open a second socket if one is already connecting/open
    if (
      socketRef.current &&
      (socketRef.current.readyState === WebSocket.CONNECTING ||
        socketRef.current.readyState === WebSocket.OPEN)
    ) {
      return;
    }

    const isSecure = HOST_API.includes("https");
    const wsHost = HOST_API.replace(/^https?:\/\//, "").replace(/\/+$/, "");
    const protocol = isSecure ? "wss" : "ws";
    const url = `${protocol}://${wsHost}/ws/simulation-updates/?token=${token}&test_id=${testId}`;

    const ws = new WebSocket(url);
    socketRef.current = ws;

    ws.onopen = () => {
      retriesRef.current = 0; // reset back-off on successful connect
    };

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        if (parsed?.type === "simulation_update") {
          onUpdateRef.current?.(parsed.data);
        }
      } catch {
        // ignore non-JSON
      }
    };

    ws.onerror = () => {
      logger.warn("Simulation WebSocket error");
    };

    ws.onclose = (event) => {
      // Only act if this is still the current socket — prevents stale
      // sockets (e.g. from React StrictMode double-mount) from wiping
      // the ref or triggering spurious reconnects.
      if (socketRef.current !== ws) return;
      socketRef.current = null;

      // Auth-related errors → do NOT retry
      if ([4001, 4401, 4403, 1008].includes(event.code)) {
        logger.warn("WebSocket auth/policy error:", event.code);
        return;
      }

      if (mountedRef.current) {
        const delay = Math.min(1000 * 2 ** retriesRef.current, 30000);
        retriesRef.current += 1;
        timerRef.current = setTimeout(connect, delay);
      }
    };
  }, [user?.accessToken, testId]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearTimeout(timerRef.current);
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [connect]);
};
