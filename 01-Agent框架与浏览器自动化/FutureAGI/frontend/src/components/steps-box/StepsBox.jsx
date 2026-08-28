import { Box, Typography, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const StepsBox = ({ title, stepNumber, children }) => {
  const theme = useTheme();
  const typographyTheme = theme.typography;
  const spacingTheme = theme.spacing;
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        border: `1px solid`,
        borderRadius: spacingTheme(0.5),
        borderColor: "divider",
      }}
    >
      <Box
        display={"flex"}
        flexDirection={"row"}
        alignItems={"center"}
        padding={spacingTheme(0.5)}
        gap={spacingTheme(1)}
        borderBottom={1}
        width={"100%"}
        borderColor={"divider"}
      >
        <Typography
          typography={"s2"}
          sx={{
            bgcolor: "background.neutral",
            width: "28px",
            height: "28px",
            alignContent: "center",
            textAlign: "center",
            borderRadius: spacingTheme(0.25),
          }}
        >
          {stepNumber}
        </Typography>
        <Typography
          typography={"s2"}
          fontWeight={typographyTheme.fontWeightMedium}
        >
          {title}
        </Typography>
      </Box>
      <Box>{children}</Box>
    </Box>
  );
};

export default StepsBox;

StepsBox.propTypes = {
  title: PropTypes.string,
  stepNumber: PropTypes.number,
  children: PropTypes.node,
};
