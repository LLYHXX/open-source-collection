import { Box } from "@mui/material";
import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { useParams } from "react-router";
import EvalsCardGraphs from "src/sections/develop-detail/DatasetSummaryTab/EvalsCard/EvalsCardGraphs";
import { useAgentDetailsStore } from "../store/agentDetailsStore";
import CustomAgentTabs from "../CustomAgentTabs";

const ANALYTICS_MODES = [
  {
    label: "Live Analytics",
    value: "Live",
    disabled: true,
  },
  {
    label: "Test Analytics",
    value: "Test",
  },
];

const PerformanceAnalyticsView = () => {
  const [analyticsMode, setAnalyticsMode] = useState("Test");
  const handleAnalyticsModeChange = (_event, newAnalyticsMode) => {
    if (newAnalyticsMode !== null && newAnalyticsMode !== undefined) {
      setAnalyticsMode(newAnalyticsMode);
    }
  };
  const { selectedVersion } = useAgentDetailsStore();
  const { agentDefinitionId } = useParams();

  const { data, isPending, isLoading } = useQuery({
    queryKey: ["test-analytics", selectedVersion],
    queryFn: () =>
      axios.get(
        endpoints.agentDefinitions.getTestAnalytics(
          agentDefinitionId,
          selectedVersion,
        ),
      ),
    enabled: !!agentDefinitionId && !!selectedVersion,
    select: (e) => e?.data?.result || [],
  });

  return (
    <Box display="flex" flexDirection="column" gap={2} px={2} py={1}>
      <CustomAgentTabs
        value={analyticsMode}
        onChange={handleAnalyticsModeChange}
        tabs={ANALYTICS_MODES}
      />
      <EvalsCardGraphs
        data={data}
        isPending={isPending}
        isLoading={isLoading}
        // datasetIndex={0}
        emptyComponent={<></>}
        showCriticalIssues={false}
        mode="simulate"
      />
    </Box>
  );
};

export default PerformanceAnalyticsView;
