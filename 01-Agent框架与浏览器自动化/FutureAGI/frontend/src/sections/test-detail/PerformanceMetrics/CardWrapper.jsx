import { Box, Typography } from "@mui/material";
import _ from "lodash";
import PropTypes from "prop-types";
import React from "react";

export default function CardWrapper({ children, title, sx = {}, expanded }) {
  return (
    <Box
      sx={{
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        boxShadow: "4px 4px 12px 0px #0000000A",
        height: expanded ? "fir-content" : "220px",
        overflowY: "auto",
        bgcolor: "background.paper",
        ...sx,
      }}
    >
      <Typography
        typography="s2_1"
        color="text.primary"
        fontWeight={"fontWeightMedium"}
        sx={{
          position: "sticky",
          top: 0,
          bgcolor: "background.paper",
          padding: 2,
          zIndex: 20,
        }}
      >
        {_.toUpper(title)}
      </Typography>
      <Box
        sx={{
          padding: (theme) => theme.spacing(0, 2, 2, 2),
        }}
      >
        {children}
      </Box>
    </Box>
  );
}

CardWrapper.propTypes = {
  children: PropTypes.node.isRequired,
  title: PropTypes.string.isRequired,
  sx: PropTypes.object,
  expanded: PropTypes.bool,
};
