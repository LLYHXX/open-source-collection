import { Box, Tooltip, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import SvgColor from "src/components/svg-color";

const InputSection = ({
  children,
  label,
  icon,
  tooltipText,
  sx,
  labelProps = {},
}) => {
  return (
    <Box
      sx={{
        ...sx,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <Typography
          variant="s3"
          fontWeight={"fontWeightMedium"}
          color="text.primary"
          {...labelProps}
        >
          {label}
        </Typography>
        {icon && (
          <Tooltip title={tooltipText} arrow>
            <SvgColor
              sx={{
                height: "16px",
                width: "16px",
                color: "text.primary",
              }}
              src={icon}
            />
          </Tooltip>
        )}
        {/* <Iconify icon="solar:info-circle-bold" color="text.disabled" /> */}
      </Box>
      {children}
    </Box>
  );
};

InputSection.propTypes = {
  children: PropTypes.any,
  label: PropTypes.string,
  sx: PropTypes.any,
  icon: PropTypes.string,
  tooltipText: PropTypes.string,
  labelProps: PropTypes.object,
};

export default InputSection;
