import React from "react";
import {
  getChipColor,
  getChipLabel,
  getChipTextColor,
  interpolateColorforExperiment,
  parseArrayString,
} from "./Common";
import { Box, Chip, Skeleton, Typography, useTheme } from "@mui/material";
import PropTypes from "prop-types";

export const StatusCellRenderer = ({ data, value }) => {
  // Use value from valueGetter if available, otherwise fall back to data.cellValue
  const cellData = value || data;

  const renderArray = () => {
    if (!cellData?.cellValue) {
      return (
        <Skeleton
          variant="rounded"
          width={80}
          height={24}
          sx={{ borderRadius: 1, margin: "5px" }}
        />
      );
    }

    try {
      const parsedData = parseArrayString(cellData.cellValue);
      if (Array.isArray(parsedData) && parsedData.length > 0) {
        return parsedData.slice(0, 2).map((item, index, arr) => (
          <Chip
            key={index}
            variant="soft"
            label={index === 0 ? item : ` +${arr.length - 1}`}
            size="small"
            sx={{
              margin: "5px",
              backgroundColor: "action.hover",
              color: "primary.main",
              pointerEvents: "none",
              fontWeight: "400",
              "&:hover": {
                color: "primary.main",
                backgroundColor: "action.hover",
              },
            }}
          />
        ));
      }
      return null;
    } catch (error) {
      return null;
    }
  };

  const isArray = cellData?.dataType === "array" || data?.dataType === "array";
  const isFloat = cellData?.dataType === "float" || data?.dataType === "float";
  const isError = cellData?.cellValue === "error";

  return (
    <Box>
      {isArray && !isError ? (
        renderArray()
      ) : isError ? (
        <Typography sx={{ color: "red.700", margin: "8px" }}>error</Typography>
      ) : (
        <Chip
          variant="soft"
          label={getChipLabel(cellData || data)}
          size="small"
          color={getChipColor(cellData || data)}
          sx={{
            backgroundColor:
              isFloat && cellData?.cellValue
                ? interpolateColorforExperiment(
                    parseFloat(cellData?.cellValue),
                    1,
                  )
                : undefined,
            color:
              isFloat && cellData?.cellValue
                ? getChipTextColor(parseFloat(cellData?.cellValue), 1)
                : undefined,
            pointerEvents: "none",
            margin: "5px",
          }}
        />
      )}
    </Box>
  );
};

export const ViewDetailCellRenderer = (params) => {
  const { data, setOpenDetailRow } = params;

  const theme = useTheme();

  const handleClick = () => {
    if (setOpenDetailRow && data) {
      setOpenDetailRow(data);
    }
  };

  return (
    <Box
      aria-label="open-view-detail"
      className="comparision-table-detail"
      onClick={handleClick}
      style={{
        color: theme.palette.primary.main,
        cursor: "pointer",
        pointerEvents: "auto",
        fontWeight: 400,
        fontSize: "14px",
      }}
    >
      View Detail
    </Box>
  );
};

StatusCellRenderer.propTypes = {
  data: PropTypes.object,
  value: PropTypes.object,
};

ViewDetailCellRenderer.propTypes = {
  data: PropTypes.object,
  setOpenDetailRow: PropTypes.func,
};
