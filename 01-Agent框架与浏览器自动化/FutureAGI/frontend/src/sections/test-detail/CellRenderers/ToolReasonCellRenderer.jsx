import { Box, Skeleton } from "@mui/material";
import React from "react";
import { ToolEvalStatus } from "../common";
import CellMarkdown from "src/sections/common/CellMarkdown";
import CustomTooltip from "src/components/tooltip/CustomTooltip";
import FormattedValueReason from "src/sections/evals/EvaluationsTabs/FormattedReason";
import PropTypes from "prop-types";
import EvaluationReasonFallback from "src/sections/common/EvaluationReasonFallback";

const ToolReasonCellRenderer = ({ value: evalData }) => {
  const renderContent = () => {
    if (evalData?.status === ToolEvalStatus.RUNNING)
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

    if (evalData?.status === ToolEvalStatus.FAILED || evalData?.error)
      return <EvaluationReasonFallback message={evalData?.value} />;

    return (
      <Box
        sx={{
          lineHeight: "1.5",
          overflow: "hidden",
          textOverflow: "ellipsis",
          WebkitLineClamp: 6,
          WebkitBoxOrient: "vertical",
        }}
      >
        <CellMarkdown text={evalData?.reason || ""} spacing={0} />
      </Box>
    );
  };

  return (
    <CustomTooltip
      show={evalData?.reason?.length}
      placement="bottom"
      title={FormattedValueReason(evalData?.reason)}
      arrow
      size="small"
    >
      <Box sx={{ height: "100%", width: "100%" }}>{renderContent()}</Box>
    </CustomTooltip>
  );
};

ToolReasonCellRenderer.propTypes = {
  data: PropTypes.object,
  value: PropTypes.any,
  column: PropTypes.object,
};

export default ToolReasonCellRenderer;
