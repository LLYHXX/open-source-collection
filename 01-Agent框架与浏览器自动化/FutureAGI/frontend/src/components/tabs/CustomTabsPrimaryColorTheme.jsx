import { Box, useTheme, Tab, Tabs } from "@mui/material";
import PropTypes from "prop-types";
import React, { useMemo } from "react";

const CustomTabsPrimaryColorTheme = ({ value, onChange, tabs }) => {
  const theme = useTheme();

  const isDark = theme.palette.mode === "dark";

  const tabWrapperStyles = useMemo(
    () => ({
      alignSelf: "flex-start",
      border: `1px solid ${theme.palette.divider}`,
      padding: theme.spacing(0.5),
      borderRadius: "10px",
      position: "relative",
      marginBottom: theme.spacing(1),
      backgroundColor: isDark
        ? theme.palette.background.default
        : theme.palette.background.neutral,
    }),
    [theme, isDark],
  );

  const tabStyles = useMemo(
    () => ({
      paddingTop: "0px !important",
      paddingBottom: "0px !important",
      paddingLeft: "20px !important",
      paddingRight: "20px !important",
      margin: "0px !important",
      maxWidth: "max-content",
      borderRadius: "8px !important",
      position: "relative",
      fontWeight: theme.typography.fontWeightMedium,
      height: "28px !important",
      minHeight: "28px !important",
      lineHeight: "28px !important",
      color: theme.palette.text.secondary,
      fontSize: "14px",
      display: "flex !important",
      alignItems: "center",
      justifyContent: "center",
      textTransform: "none",
      transition: "all 0.2s ease",
      "&.Mui-selected": {
        backgroundColor:
          (isDark ? "#FFFFFF" : theme.palette.primary.lighter) + " !important",
        color:
          (isDark ? "#000000" : theme.palette.primary.main) + " !important",
        borderRadius: "8px !important",
        boxShadow: isDark ? "0px 1px 3px rgba(0, 0, 0, 0.12)" : "none",
      },
      "&:hover:not(.Mui-selected)": {
        backgroundColor: isDark
          ? "rgba(255, 255, 255, 0.06)"
          : "rgba(0, 0, 0, 0.04)",
      },
    }),
    [theme, isDark],
  );

  return (
    <Box sx={tabWrapperStyles}>
      <Tabs
        value={value}
        onChange={onChange}
        TabIndicatorProps={{ style: { display: "none" } }}
        sx={{
          minHeight: "32px !important",
          height: "32px !important",
          padding: "0px !important",
          margin: "0px !important",
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-start",
          "& .MuiTabs-flexContainer": {
            gap: "0px",
            alignItems: "center",
            height: "100%",
          },
          "& .MuiTab-root": tabStyles,
        }}
      >
        {tabs.map((tab) => (
          <Tab
            key={tab.value}
            label={tab.label}
            value={tab.value}
            disabled={tab.disabled}
          />
        ))}
      </Tabs>
    </Box>
  );
};

CustomTabsPrimaryColorTheme.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  tabs: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      value: PropTypes.string.isRequired,
      disabled: PropTypes.bool,
    }),
  ).isRequired,
};

export default CustomTabsPrimaryColorTheme;
