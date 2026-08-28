import React, { useCallback, useEffect, useState } from "react";
import CustomAgentTabs from "../CustomAgentTabs";
import { Box } from "@mui/material";
import { CALL_LOGS_TAB_IDS, callLogsTabData } from "../constants";
import CallLogsGrid from "./CallLogsGrid";
import { useParams } from "react-router";
import { useTestDetailSideDrawerStoreShallow } from "src/sections/test-detail/states";
import { transformMetricDetails } from "./utils";
import { useUrlState } from "src/routes/hooks/use-url-state";
import PropTypes from "prop-types";
import LiveCallMonitor from "src/components/live-call-monitor/LiveCallMonitor";

const CallLogsView = ({ agentType }) => {
  const [activeTab, setActiveTab] = useState("test");
  const [liveCallId, setLiveCallId] = useState(null);

  // Listen for "Listen" button clicks from the cell renderer
  const handleLiveCallEvent = useCallback((e) => {
    setLiveCallId(e.detail?.callId || null);
  }, []);

  useEffect(() => {
    window.addEventListener("open-live-call-monitor", handleLiveCallEvent);
    return () =>
      window.removeEventListener("open-live-call-monitor", handleLiveCallEvent);
  }, [handleLiveCallEvent]);
  const { agentDefinitionId } = useParams();
  const [, setUrlRowIndex] = useUrlState("rowIndex");
  const { setTestDetailDrawerOpen } = useTestDetailSideDrawerStoreShallow(
    (state) => ({
      setTestDetailDrawerOpen: state.setTestDetailDrawerOpen,
    }),
  );

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleRowClicked = (params, page, pageLimit = 10) => {
    const localIndex = params.rowIndex;
    const globalIndex = (page - 1) * pageLimit + localIndex;

    const data = params?.data;
    if (!data) return;

    const { metricDetails, evalMetrics } = transformMetricDetails(data);
    setUrlRowIndex({
      rowIndex: globalIndex,
      origin: "agent-definition",
      module: "simulate",
    });
    setTestDetailDrawerOpen({
      ...metricDetails,
      evalMetrics,
      ignoreCache: true,
    });
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        px: 2,
        py: 1,
        gap: 2,
        minHeight: 0,
      }}
    >
      <CustomAgentTabs
        value={activeTab}
        onChange={handleTabChange}
        tabs={callLogsTabData(agentType)}
      />

      <Box sx={{ flex: 1, minHeight: 0 }}>
        {/* Tab content below */}
        {activeTab === CALL_LOGS_TAB_IDS.LIVE_CALL_LOGS && (
          <CallLogsGrid id={agentDefinitionId} />
        )}
        {activeTab === CALL_LOGS_TAB_IDS.TEST_CALL_LOGS && (
          <CallLogsGrid
            agentType={agentType}
            id={agentDefinitionId}
            onRowClicked={handleRowClicked}
          />
        )}
      </Box>

      <LiveCallMonitor
        callId={liveCallId}
        open={Boolean(liveCallId)}
        onClose={() => setLiveCallId(null)}
      />
    </Box>
  );
};
CallLogsView.propTypes = {
  agentType: PropTypes.string,
};

export default CallLogsView;
