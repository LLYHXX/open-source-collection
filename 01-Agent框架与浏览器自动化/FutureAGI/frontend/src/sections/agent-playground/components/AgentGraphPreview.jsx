import React, { useMemo } from "react";
import PropTypes from "prop-types";
import { ReactFlowProvider } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useGetVersionDetail } from "src/api/agent-playground/agent-playground";
import { parseVersionResponse } from "../utils/versionPayloadUtils";
import {
  PreviewContainer,
  PreviewGraphInner,
  PreviewLoading,
  PreviewError,
} from "./PreviewGraphInner";

export default function AgentGraphPreview({
  agentId,
  versionId,
  versionData: externalData,
}) {
  const {
    data: fetchedData,
    isLoading,
    isError,
  } = useGetVersionDetail(agentId, versionId, {
    enabled: !externalData,
  });

  const data = externalData || fetchedData;

  const graphData = useMemo(() => {
    if (!data) return null;
    return parseVersionResponse(data);
  }, [data]);

  const isEnabled = Boolean(externalData || (agentId && versionId));

  if (!isEnabled) {
    return null;
  }

  if (!externalData && isLoading) {
    return <PreviewLoading />;
  }

  if (!externalData && isError) {
    return <PreviewError />;
  }

  if (!graphData) {
    return null;
  }

  return (
    <PreviewContainer>
      <ReactFlowProvider>
        <PreviewGraphInner
          fitView
          fitViewOptions={{ padding: 0.2, maxZoom: 1 }}
          nodes={graphData.nodes}
          edges={graphData.edges}
        />
      </ReactFlowProvider>
    </PreviewContainer>
  );
}

AgentGraphPreview.propTypes = {
  agentId: PropTypes.string,
  versionId: PropTypes.string,
  versionData: PropTypes.object,
};
