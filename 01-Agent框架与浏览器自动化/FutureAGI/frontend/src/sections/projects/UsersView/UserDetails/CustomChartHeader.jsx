import { Box, Typography, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import React, { useMemo } from "react";
import {
  CustomTab,
  CustomTabs,
  TabWrapper,
} from "src/sections/develop/AddDatasetDrawer/AddDatasetStyle";

const CustomChartHeader = ({ label, chartType, onToggleType, totalTraces }) => {
  const theme = useTheme();

  const tabWrapperStyles = useMemo(
    () => ({
      alignSelf: "flex-start",
      backgroundColor: "background.neutral",
      border: 0,
      padding: theme.spacing(0),
      borderRadius: "4px",
      position: "relative",
    }),
    [theme],
  );

  const tabStyles = useMemo(
    () => ({
      paddingTop: theme.spacing(0.5),
      paddingBottom: theme.spacing(0.5),
      margin: theme.spacing(0.5),
      borderRadius: "4px",
      position: "relative",
      fontWeight: 500,
      minHeight: "auto",
      color: theme.palette.text.disabled,
      "&.Mui-selected": {
        backgroundColor: "var(--bg-paper) !important",
        boxShadow: "3px 3px 6px rgba(0, 0, 0, 0.12)",
        color: "text.primary",
      },
    }),
    [theme],
  );

  return (
    <Box px={2}>
      {/* Top Row: Label and Tab Toggle */}
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Typography
          variant="m2"
          fontWeight="fontWeightMedium"
          color={theme.palette.text.primary}
        >
          {label}
        </Typography>

        {/* Add container with proper spacing for shadow */}
        <Box>
          <TabWrapper sx={tabWrapperStyles}>
            <CustomTabs
              value={chartType}
              onChange={(e, value) => onToggleType(value)}
              TabIndicatorProps={{ style: { display: "none" } }}
              sx={{
                minHeight: "auto", // Remove default tabs height
                "& .MuiTabs-flexContainer": {
                  gap: theme.spacing(0.25), // Small gap between tabs
                },
              }}
            >
              <CustomTab label="Line" value="line" sx={tabStyles} />
              <CustomTab label="Bar" value="bar" sx={tabStyles} />
            </CustomTabs>
          </TabWrapper>
        </Box>
      </Box>

      {/* Bottom Row: Total Traces */}
      <Box>
        <Typography variant="body2" color="text.disabled">
          <Box component="span" fontWeight="fontWeightMedium" color="green.500">
            {totalTraces}
          </Box>{" "}
          Total {label}
        </Typography>
      </Box>
    </Box>
  );
};

CustomChartHeader.propTypes = {
  label: PropTypes.string,
  chartType: PropTypes.string,
  onToggleType: PropTypes.func,
  totalTraces: PropTypes.any,
};

export default CustomChartHeader;
