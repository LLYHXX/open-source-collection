import { Box, Chip, styled } from "@mui/material";
import { alpha } from "@mui/material/styles";
import PropTypes from "prop-types";
import React from "react";

const StyledChip = styled(Chip, {
  shouldForwardProp: (prop) => prop !== "isSelected",
})(({ theme, isSelected }) => {
  const isDark = theme.palette.mode === "dark";
  return {
    borderRadius: "100px",
    height: "auto",
    cursor: "pointer",
    padding: "3px 12px",
    transition: "all 0.2s ease",
    border: `1px solid ${
      isSelected
        ? isDark
          ? theme.palette.purple[500]
          : theme.palette.purple[200]
        : isDark
          ? theme.palette.border.default
          : theme.palette.grey[300]
    }`,
    backgroundColor: isSelected
      ? isDark
        ? alpha(theme.palette.purple[500], 0.2)
        : theme.palette.purple.o20
      : "transparent",
    color: "text.primary",
    "&:hover": {
      backgroundColor: isSelected
        ? isDark
          ? alpha(theme.palette.purple[500], 0.3)
          : alpha(theme.palette.purple[500], 0.15)
        : theme.palette.action.hover,
      borderColor: isDark
        ? theme.palette.border.hover
        : theme.palette.grey[400],
    },
    "& .MuiChip-label": {
      typography: theme.typography.s1,
      fontWeight: theme.typography.fontWeightMedium,
      color: theme.palette.text.primary,
      padding: 0,
    },
  };
});

const ChipSelector = ({
  options = [],
  value,
  onChange,
  sx = {},
  chipSx = {},
  ...rest
}) => {
  const handleChipClick = (optionValue) => {
    if (onChange) {
      onChange(optionValue);
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        gap: 1,
        flexWrap: "wrap",
        ...sx,
      }}
      {...rest}
    >
      {options.map((option) => (
        <StyledChip
          key={option.value}
          label={option.label}
          isSelected={value === option.value}
          onClick={() => handleChipClick(option.value)}
          sx={chipSx}
        />
      ))}
    </Box>
  );
};

ChipSelector.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      value: PropTypes.string.isRequired,
    }),
  ).isRequired,
  value: PropTypes.string,
  onChange: PropTypes.func,
  sx: PropTypes.object,
  chipSx: PropTypes.object,
};

export default ChipSelector;
