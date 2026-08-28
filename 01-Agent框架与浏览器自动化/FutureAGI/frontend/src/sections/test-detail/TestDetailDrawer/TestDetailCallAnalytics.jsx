import { Box, Divider, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React, { useMemo } from "react";
import TestDetailSystemMetrics from "./TestDetailSystemMetrics";
import { ShowComponent } from "src/components/show";
import TestDetailCostBreakdown from "./TestDetailCostBreakdown";
import { isCellValueEmpty } from "src/components/table/utils";
import { isLiveKitProvider } from "src/sections/agents/constants";

const TestDetailCallAnalytics = ({
  latencies,
  analysisSummary,
  costBreakdown,
  provider,
}) => {
  const isLiveKit = isLiveKitProvider(provider);

  const allLatenciesPresent = useMemo(() => {
    return (
      !isCellValueEmpty(Math.ceil(latencies?.endpointing)) ||
      !isCellValueEmpty(Math.ceil(latencies?.transcriber)) ||
      !isCellValueEmpty(Math.ceil(latencies?.model)) ||
      !isCellValueEmpty(Math.ceil(latencies?.voice))
    );
  }, [latencies]);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <ShowComponent
        condition={
          !analysisSummary && !latencies && !costBreakdown && !isLiveKit
        }
      >
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            height: "200px",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <Typography typography="s1" fontWeight="fontWeightMedium">
            No call analytics data available
          </Typography>
        </Box>
      </ShowComponent>
      <ShowComponent condition={analysisSummary}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <Typography typography="s1_2" fontWeight="fontWeightMedium">
            Analysis Summary
          </Typography>
          <Box
            sx={{
              border: "1px solid",
              borderColor: "divider",
              backgroundColor: "background.neutral",
              borderRadius: "4px",
              paddingX: "14px",
              paddingY: "14px",
            }}
          >
            <Typography typography="s1_2">{analysisSummary}</Typography>
          </Box>
        </Box>
      </ShowComponent>
      <ShowComponent condition={isLiveKit}>
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: "4px",
          }}
        >
          <Typography typography="s1_2" fontWeight="fontWeightMedium">
            System Metrics & Cost Breakdown
          </Typography>
          <Box
            sx={{
              border: "1px solid",
              borderColor: "divider",
              backgroundColor: "background.neutral",
              borderRadius: "4px",
              paddingX: "14px",
              paddingY: "14px",
            }}
          >
            <Typography typography="s1_2" color="text.secondary">
              System metrics breakdown and cost breakdown are not available for
              LiveKit agents. LiveKit does not expose internal pipeline metrics
              or billing data via API.
            </Typography>
          </Box>
        </Box>
      </ShowComponent>
      <ShowComponent condition={!isLiveKit && allLatenciesPresent}>
        <TestDetailSystemMetrics latencies={latencies} />
      </ShowComponent>
      <ShowComponent condition={!isLiveKit && costBreakdown}>
        <Divider />
        <TestDetailCostBreakdown costBreakdown={costBreakdown} />
      </ShowComponent>
    </Box>
  );
};

TestDetailCallAnalytics.propTypes = {
  latencies: PropTypes.shape({
    model: PropTypes.number,
    voice: PropTypes.number,
    transcriber: PropTypes.number,
    endpointing: PropTypes.number,
  }),
  analysisSummary: PropTypes.string,
  costBreakdown: PropTypes.shape({
    llm: PropTypes.shape({
      cost: PropTypes.number,
      promptTokens: PropTypes.number,
      completionTokens: PropTypes.number,
    }),
    stt: PropTypes.shape({
      cost: PropTypes.number,
    }),
    tts: PropTypes.shape({
      cost: PropTypes.number,
    }),
  }),
  provider: PropTypes.string,
};

export default TestDetailCallAnalytics;
