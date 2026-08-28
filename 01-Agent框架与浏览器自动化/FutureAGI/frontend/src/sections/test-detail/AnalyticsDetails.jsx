import { useQuery } from "@tanstack/react-query";
import React from "react";
import { useParams } from "react-router";
import axios, { endpoints } from "src/utils/axios";
import EvalsCardGraphs from "../develop-detail/DatasetSummaryTab/EvalsCard/EvalsCardGraphs";
import { Box } from "@mui/material";

const AnalyticsDetails = () => {
  const { testId, executionId } = useParams();
  const { data, isPending, isLoading } = useQuery({
    queryKey: ["test-execution-analytics", testId],
    queryFn: () =>
      axios.get(endpoints.testExecutions.executionAnalytics(testId), {
        params: {
          execution_id: executionId,
        },
      }),

    select: (e) => e?.data?.result || [],
  });

  return (
    <Box
      sx={{
        paddingX: 2,
        overflow: "auto",
        paddingTop: 1,
        zIndex: 2,
        backgroundColor: "background.paper",
      }}
    >
      <EvalsCardGraphs
        data={data}
        isPending={isPending}
        isLoading={isLoading}
        emptyComponent={<></>}
        mode="simulate"
      />
    </Box>
  );
};

export default AnalyticsDetails;
