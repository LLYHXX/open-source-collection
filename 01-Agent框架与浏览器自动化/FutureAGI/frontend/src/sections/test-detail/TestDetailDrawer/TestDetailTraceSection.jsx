import { useQuery } from "@tanstack/react-query";
import PropTypes from "prop-types";
import React from "react";
import TraceTree from "src/components/traceDetailDrawer/trace-tree";
import axios, { endpoints } from "src/utils/axios";
import { columnOptions } from "../common";
import LoadingStateComponent from "src/components/CallLogsDetailDrawer/LoadingStateComponent";
import { Box, Typography } from "@mui/material";
import { SelectedNodeProvider } from "src/components/traceDetailDrawer/selectedNodeContext";

const TestDetailTraceSection = ({ data }) => {
  const traceIdForFetch =
    data?.trace_details?.trace_id ?? data?.traceDetails?.traceId;
  const { data: traceDetail, isLoading } = useQuery({
    queryKey: ["trace-detail", traceIdForFetch],
    queryFn: () => {
      return axios.get(endpoints.project.getTrace(traceIdForFetch));
    },
    enabled: traceIdForFetch !== undefined,
    select: (data) => data.data?.result,
  });

  if (isLoading) {
    return (
      <LoadingStateComponent message={"Loading traces..."} status="fetching" />
    );
  }

  const spans = traceDetail?.observationSpans || [];

  if (!spans.length) {
    return (
      <Box
        sx={{
          padding: 2,
          display: "flex",
          height: "200px",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Typography typography="s2_1" fontWeight="fontWeightMedium">
          No traces available
        </Typography>
      </Box>
    );
  }

  return (
    <SelectedNodeProvider>
      <TraceTree
        treeData={spans}
        disableOnClick={true}
        columnOptionItems={columnOptions}
      />
    </SelectedNodeProvider>
  );
};

TestDetailTraceSection.propTypes = {
  data: PropTypes.object,
};
export default TestDetailTraceSection;
