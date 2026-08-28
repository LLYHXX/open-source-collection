import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const PageHeadings = ({ title, description }) => {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      {title && (
        <Typography
          color="text.primary"
          variant="m2"
          fontWeight={"fontWeightSemiBold"}
        >
          {title}
        </Typography>
      )}
      {description && (
        <Box sx={{ display: "flex", gap: 0.5, alignItems: "center" }}>
          {/* <Iconify icon="solar:info-circle-bold" color="text.secondary" /> */}
          <Typography
            variant="s1"
            color="text.secondary"
            fontWeight={"fontWeightRegular"}
          >
            {description}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default PageHeadings;

PageHeadings.propTypes = {
  title: PropTypes.string,
  description: PropTypes.any,
};
