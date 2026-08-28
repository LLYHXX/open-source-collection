import { Box, Typography, alpha, useTheme } from "@mui/material";
import { format } from "date-fns";
import PropTypes from "prop-types";
import React from "react";

const OptimizationCard = ({ optimization, selected, onClick }) => {
  const theme = useTheme();

  const getStatusColor = (status) => {
    switch (status) {
      case "Completed":
        return {
          color: "success.main",
          bgcolor: alpha(theme.palette.success.main, 0.08),
          border: `1px solid ${alpha(theme.palette.success.main, 0.16)}`,
        };
      case "Running":
        return {
          color: "error.main",
          bgcolor: alpha(theme.palette.warning.main, 0.08),
          border: `1px solid ${alpha(theme.palette.warning.main, 0.16)}`,
        };
      default:
        return {
          color: "text.secondary",
          bgcolor: "background.neutral",
          border: `1px solid ${theme.palette.divider}`,
        };
    }
  };

  const statusStyle = getStatusColor(optimization.status);

  return (
    <Box
      sx={{
        width: "100%",
        padding: 1,
        border: "2px solid",
        borderColor: selected ? "primary.light" : "divider",
        borderRadius: "8px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        cursor: "pointer",
      }}
      onClick={onClick}
    >
      <Box sx={{ width: "50%", overflow: "hidden" }}>
        <Typography
          fontWeight={500}
          fontSize="14px"
          variant="subtitle2"
          noWrap
          sx={{
            textOverflow: "ellipsis",
            overflow: "hidden",
            display: "block",
          }}
          title={optimization.name}
        >
          {optimization.name}
        </Typography>
      </Box>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1,
          flex: 1,
          justifyContent: "flex-end",
        }}
      >
        <Typography
          fontWeight={400}
          fontSize="14px"
          variant="subtitle2"
          sx={{
            bgcolor: statusStyle.bgcolor,
            padding: "4px 8px",
            borderRadius: "12px",
            ...(statusStyle.border && { border: statusStyle.border }),
            whiteSpace: "nowrap",
          }}
        >
          {optimization.status}
        </Typography>
        <Typography
          fontWeight={400}
          fontSize="13px"
          variant="subtitle2"
          sx={{ whiteSpace: "nowrap" }}
        >
          {format(new Date(optimization.created_at), "dd-MM-yy")}
        </Typography>
      </Box>
    </Box>
  );
};

OptimizationCard.propTypes = {
  optimization: PropTypes.object.isRequired,
  selected: PropTypes.bool,
  onClick: PropTypes.func,
};

export default OptimizationCard;
