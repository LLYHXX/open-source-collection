import { Box, Skeleton } from "@mui/material";
import React from "react";
import CellMarkdown from "src/sections/common/CellMarkdown";
import CustomTooltip from "src/components/tooltip/CustomTooltip";
import FormattedValueReason from "src/sections/evals/EvaluationsTabs/FormattedReason";
import { CallExecutionLoadingStatus, TestRunLoadingStatus } from "../common";
import PropTypes from "prop-types";
import EvaluationReasonFallback from "src/sections/common/EvaluationReasonFallback";

const EvalReasonCellRenderer = ({ value: evalData }) => {
  const renderContent = () => {
    const {
      overall_status: _overallStatus,
      call_status: _callStatus,
      ...restEvalData
    } = evalData || {};

    if (evalData?.error) {
      return <EvaluationReasonFallback message={evalData?.value} />;
    }

    const hasEvalData = Object.keys(restEvalData).length > 0;
    const callLoading = CallExecutionLoadingStatus.includes(
      evalData?.call_status?.toLowerCase(),
    );
    const runLoading = TestRunLoadingStatus.includes(
      evalData?.overall_status?.toLowerCase(),
    );
    if (!hasEvalData && (callLoading || runLoading)) {
      return (
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            height: "100%",
            width: "100%",
          }}
        >
          <Skeleton sx={{ width: "100%", height: "20px" }} variant="rounded" />
        </Box>
      );
    }

    return (
      <Box
        sx={{
          lineHeight: "1.5",
          overflow: "hidden",
          textOverflow: "ellipsis",
          WebkitLineClamp: 6,
          WebkitBoxOrient: "vertical",
          whiteSpace: "pre-wrap",
        }}
      >
        <CellMarkdown text={restEvalData?.reason || ""} />
      </Box>
    );
  };

  const {
    overall_status: _overallStatus,
    call_status: _callStatus,
    ...restEvalData
  } = evalData || {};
  return (
    <CustomTooltip
      show={restEvalData?.reason?.length}
      placement="bottom"
      title={FormattedValueReason(restEvalData?.reason)}
      arrow
      size="small"
    >
      <Box sx={{ height: "100%", width: "100%" }}>{renderContent()}</Box>
    </CustomTooltip>
  );
};

EvalReasonCellRenderer.propTypes = {
  data: PropTypes.object,
  value: PropTypes.any,
  column: PropTypes.object,
};

export default EvalReasonCellRenderer;
