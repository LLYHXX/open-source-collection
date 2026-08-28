import { useEffect, useRef } from "react";
import axios, { endpoints } from "src/utils/axios";
import useImagineStore from "./useImagineStore";

/**
 * Background analysis for dynamic widgets via REST API + DB polling.
 *
 * Flow:
 * 1. Detect widgets with `dynamicAnalysis` that have no cached result
 * 2. POST /tracer/imagine-analysis/ to trigger background LLM analysis
 * 3. Poll GET /tracer/imagine-analysis/ every 3s until complete
 * 4. Cache results in store (also persisted in DB for reload)
 */
export default function useDynamicAnalysis(
  widgets,
  traceData,
  _chatRef,
  traceId,
) {
  const triggeredRef = useRef(new Set());
  const pollIntervalRef = useRef(null);
  const savedViewId = useImagineStore((s) => s._savedViewId);

  // Main trigger effect
  useEffect(() => {
    if (!widgets?.length || !traceId || !traceData || !savedViewId) return;

    const store = useImagineStore.getState();

    const needsRun = widgets.filter((w) => {
      if (!w.dynamicAnalysis) return false;
      if (store.getAnalysis(traceId, w.id)) return false;
      if (triggeredRef.current.has(`${traceId}::${w.id}`)) return false;
      return true;
    });

    if (!needsRun.length) {
      // Nothing to trigger — but check if there are pending results in DB to poll
      const hasPending = widgets.some(
        (w) => w.dynamicAnalysis && !store.getAnalysis(traceId, w.id),
      );
      if (hasPending && !pollIntervalRef.current) {
        startPolling(traceId, savedViewId, pollIntervalRef);
      }
      return;
    }

    // Mark as triggered
    needsRun.forEach((w) => triggeredRef.current.add(`${traceId}::${w.id}`));

    // Extract project_id from URL
    const pathParts = window.location.pathname.split("/");
    const observeIdx = pathParts.indexOf("observe");
    const projectId = observeIdx >= 0 ? pathParts[observeIdx + 1] : null;

    // Trigger analysis via API
    triggerAnalysis(needsRun, traceId, savedViewId, projectId);

    // Start polling for results
    startPolling(traceId, savedViewId, pollIntervalRef);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [widgets, traceData, traceId, savedViewId]);

  // Reset when trace changes
  const prevTraceRef = useRef(traceId);
  useEffect(() => {
    if (traceId !== prevTraceRef.current) {
      prevTraceRef.current = traceId;
      triggeredRef.current.clear();
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }
  }, [traceId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, []);
}

async function triggerAnalysis(widgets, traceId, savedViewId, projectId) {
  try {
    const response = await axios.post(endpoints.imagineAnalysis.trigger, {
      saved_view_id: savedViewId,
      trace_id: traceId,
      project_id: projectId,
      widgets: widgets.map((w) => ({
        widget_id: w.id,
        prompt: w.dynamicAnalysis.prompt,
      })),
    });

    // If any already completed (cached in DB from previous run), store them
    const analyses = response.data?.result?.analyses || [];
    const store = useImagineStore.getState();
    analyses.forEach((a) => {
      if (a.status === "completed" && a.content) {
        store.setAnalysis(traceId, a.widgetId || a.widget_id, a.content);
      }
    });
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error("Failed to trigger analysis:", err);
  }
}

function startPolling(traceId, savedViewId, intervalRef) {
  if (intervalRef.current) return;

  let failures = 0;

  intervalRef.current = setInterval(async () => {
    try {
      const response = await axios.get(endpoints.imagineAnalysis.poll, {
        params: { saved_view_id: savedViewId, trace_id: traceId },
      });

      const analyses = response.data?.result?.analyses || [];
      const store = useImagineStore.getState();

      let allDone = true;
      analyses.forEach((a) => {
        const widgetId = a.widgetId || a.widget_id;
        if (a.status === "completed" && a.content) {
          store.setAnalysis(traceId, widgetId, a.content);
        } else if (a.status === "failed") {
          store.setAnalysis(
            traceId,
            widgetId,
            `*Analysis failed: ${a.error || "Unknown error"}. Click Rerun to retry.*`,
          );
        } else {
          allDone = false;
        }
      });

      if (allDone || analyses.length === 0) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }

      failures = 0;
    } catch {
      failures++;
      if (failures > 10) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
  }, 3000);
}

/**
 * Trigger re-analysis for a single widget (Rerun button).
 */
export function runAnalysis(widget, traceId) {
  if (!widget?.dynamicAnalysis?.prompt || !traceId) return false;

  const store = useImagineStore.getState();
  const savedViewId = store._savedViewId;

  // Clear cache so skeleton shows
  store.setAnalysis(traceId, widget.id, null);

  // Extract project_id
  const pathParts = window.location.pathname.split("/");
  const observeIdx = pathParts.indexOf("observe");
  const projectId = observeIdx >= 0 ? pathParts[observeIdx + 1] : null;

  // Trigger via API
  triggerAnalysis([widget], traceId, savedViewId, projectId);

  return true;
}
