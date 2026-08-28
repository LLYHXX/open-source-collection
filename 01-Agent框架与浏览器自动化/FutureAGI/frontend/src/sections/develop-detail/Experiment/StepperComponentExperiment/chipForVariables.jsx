import { Chip, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import SvgColor from "src/components/svg-color";

const getStatusConfig = (status, isDark) => {
  const configs = {
    all: {
      icon: "/assets/icons/ic_tick.svg",
      label: "All Mapped",
    },
    partial: {
      icon: "/assets/icons/ic_warning.svg",
      label: "Partially Mapped",
    },
    none: {
      icon: "/assets/icons/ic_failed.svg",
      label: "Not Mapped",
    },
  };
  const colorMap = {
    all: {
      color: isDark ? "green.400" : "green.700",
      bgColor: isDark ? "green.o20" : "green.o10",
    },
    partial: {
      color: isDark ? "orange.400" : "orange.700",
      bgColor: isDark ? "orange.o20" : "orange.o10",
    },
    none: {
      color: isDark ? "red.400" : "red.700",
      bgColor: isDark ? "red.o20" : "red.o10",
    },
  };
  return { ...configs[status], ...colorMap[status] };
};

const ChipForVariables = ({ status }) => {
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";
  const { icon, label, bgColor, color } = getStatusConfig(status, isDark);
  return (
    <Chip
      size="small"
      label={label}
      sx={{
        backgroundColor: bgColor,
        padding: "4px 8px",
        color: color,
        borderRadius: 0,
        "& .MuiChip-icon": {
          color: color,
        },
        ":hover": {
          backgroundColor: bgColor,
          color: color,
        },
      }}
      icon={<SvgColor src={icon} sx={{ width: 16, height: 16 }} />}
    />
  );
};

export default ChipForVariables;
ChipForVariables.propTypes = {
  status: PropTypes.string,
};
