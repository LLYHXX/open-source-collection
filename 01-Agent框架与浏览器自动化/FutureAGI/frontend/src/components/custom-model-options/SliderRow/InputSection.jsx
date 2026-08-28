import { Box, Typography } from "@mui/material";
import _ from "lodash";
import PropTypes from "prop-types";
import React from "react";
import CustomTooltip from "src/components/tooltip";
import SvgColor from "src/components/svg-color";

const InputSection = ({ children, label, icon, tooltipText, sx }) => {
  return (
    <Box
      sx={{
        ...sx,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
        <Typography
          variant="s3"
          fontWeight={"fontWeightMedium"}
          color="text.primary"
          className="slider-label"
        >
          {_.startCase(label)}
        </Typography>
        {icon && (
          <CustomTooltip
            type="black"
            size="small"
            show
            arrow
            title={tooltipText}
          >
            <SvgColor
              sx={{
                height: "16px",
                width: "16px",
              }}
              src="/assets/icons/ic_info.svg"
            />
          </CustomTooltip>
        )}
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
};

export default InputSection;
