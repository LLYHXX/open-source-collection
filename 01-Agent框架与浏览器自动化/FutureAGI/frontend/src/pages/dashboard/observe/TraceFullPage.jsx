import React, { useCallback } from "react";
import { useParams, useNavigate } from "react-router";
import { Helmet } from "react-helmet-async";
import TraceDetailDrawerV2 from "src/components/traceDetail/TraceDetailDrawerV2";

export default function TraceFullPage() {
  const { observeId, traceId } = useParams();
  const navigate = useNavigate();

  const handleClose = useCallback(() => {
    if (window.history.length > 1) {
      navigate(-1);
    } else if (observeId) {
      navigate(`/dashboard/observe/${observeId}/llm-tracing`);
    } else {
      window.close();
    }
  }, [navigate, observeId]);

  return (
    <>
      <Helmet>
        <title>Trace — {traceId?.substring(0, 8) || "..."}</title>
      </Helmet>
      <TraceDetailDrawerV2
        open
        traceId={traceId}
        projectId={observeId}
        onClose={handleClose}
        hasPrev={false}
        hasNext={false}
        initialFullscreen
      />
    </>
  );
}
