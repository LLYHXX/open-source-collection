import { useNavigate, useLocation } from "react-router";
import { useLLMTracingStoreShallow } from "../states";

export const useNavigationHandlers = (projectId, traceIdFromRow) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setTraceDetailDrawerOpen, setSpanDetailDrawerOpen } =
    useLLMTracingStoreShallow((state) => ({
      setTraceDetailDrawerOpen: state.setTraceDetailDrawerOpen,
      setSpanDetailDrawerOpen: state.setSpanDetailDrawerOpen,
    }));

  const handleTraceClick = (traceId) => {
    if (!projectId || !traceId) return;

    const targetPath = `/dashboard/observe/${projectId}/llm-tracing`;
    const traceDetailDrawerOpen = {
      traceId,
      filters: [],
    };

    // If we're not on the target route, navigate first
    if (location.pathname !== targetPath) {
      navigate(targetPath);
    }

    // Use the store setter which automatically updates both state and URL
    setTraceDetailDrawerOpen(traceDetailDrawerOpen);
  };

  const handleSpanClick = (spanId) => {
    if (!projectId || !traceIdFromRow) return;

    const targetPath = `/dashboard/observe/${projectId}/llm-tracing`;
    const spanDetailDrawerOpen = {
      traceId: traceIdFromRow,
      spanId,
      filters: [],
    };

    // If we're not on the target route, navigate first with selectedTab
    if (location.pathname !== targetPath) {
      const url = new URL(targetPath, window.location.origin);
      url.searchParams.set("selectedTab", "spans");
      navigate(`${url.pathname}${url.search}`);
    }

    // Use the store setter which automatically updates both state and URL
    setSpanDetailDrawerOpen(spanDetailDrawerOpen);
  };

  return { handleTraceClick, handleSpanClick };
};
