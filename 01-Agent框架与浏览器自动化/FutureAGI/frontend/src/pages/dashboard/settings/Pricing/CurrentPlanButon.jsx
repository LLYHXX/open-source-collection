import { Typography, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const CurrentPlanButton = ({ planType }) => {
  const theme = useTheme();

  const gradientColor =
    theme.palette.mode === "light"
      ? "linear-gradient(to right, var(--primary-main) 0%, #CF6BE8 100%)"
      : "linear-gradient(to right, #FFFFFF 0%, #E6E6E7 100%)";

  return (
    <Typography
      sx={{
        position: "relative",
        fontWeight: 600,
        fontSize: "16px",
        padding: "8px 40px",
        color: planType === "custom" ? "primary.main" : "primary.contrastText",
        alignSelf: "center",

        borderTopRightRadius: "8px",
        borderBottomLeftRadius: "12px",
        backgroundColor: planType === "custom" ? "background.paper" : undefined,

        background: planType !== "custom" && gradientColor,
      }}
    >
      Current plan
    </Typography>
  );
};

CurrentPlanButton.propTypes = {
  planType: PropTypes.string,
};

export default CurrentPlanButton;
