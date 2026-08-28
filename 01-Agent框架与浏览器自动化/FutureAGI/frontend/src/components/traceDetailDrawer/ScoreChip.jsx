import React from "react";
import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";
import SvgColor from "../svg-color";
import CustomTooltip from "../tooltip/CustomTooltip";
import FormattedValueReason from "src/sections/evals/EvaluationsTabs/FormattedReason";

const ScoreChip = ({
  score,
  description,
  total,
  label,
  startIcon,
  onClick = () => {},
  endIcon = (
    <SvgColor
      src="/assets/icons/ic_info.svg"
      sx={{ width: "16px", height: "16px", color: "inherit" }}
    />
  ),
}) => {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        flexDirection: "row",
        borderRadius: 0.5,
        gap: 0.5,
        p: 0.5,
        px: 1,
        color: "info.main",
        borderColor: "info.main",
        bgcolor: (theme) =>
          alpha(
            theme.palette.info.main,
            theme.palette.mode === "dark" ? 0.16 : 0.1,
          ),
      }}
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
    >
      {startIcon}
      <Typography typography={"s2"} fontWeight={500}>
        {label} {score}/{total}
      </Typography>
      <CustomTooltip
        arrow
        expandable
        show={Boolean(description?.length)}
        title={FormattedValueReason(description)}
        sx={{
          ":hover": {
            cursor: "pointer",
          },
        }}
      >
        {endIcon}
      </CustomTooltip>
    </Box>
  );
};

export default ScoreChip;

ScoreChip.propTypes = {
  score: PropTypes.number.isRequired,
  total: PropTypes.number.isRequired,
  label: PropTypes.string.isRequired,
  description: PropTypes.string,
  endIcon: PropTypes.node,
  startIcon: PropTypes.node,
  onClick: PropTypes.func,
};
