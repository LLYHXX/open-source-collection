import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const StepsHeaderComponent = ({ title, subtitle }) => {
  return (
    <Box>
      <Typography typography="m3" fontWeight={"fontWeightMedium"}>
        {title}
      </Typography>
      <Typography
        typography={"s2_1"}
        fontWeight={"fontWeightRegular"}
        color="text.secondary"
      >
        {subtitle}
      </Typography>
    </Box>
  );
};

export default StepsHeaderComponent;
StepsHeaderComponent.propTypes = {
  title: PropTypes.string,
  subtitle: PropTypes.string,
};
