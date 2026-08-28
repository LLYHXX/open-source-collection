import React from "react";
import { Box, Skeleton } from "@mui/material";
import PropTypes from "prop-types";

const GraphSkeleton = () => {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        width: "100%",
        height: "100%",
      }}
    >
      <Skeleton
        variant="rectangular"
        width="100%"
        height="100%"
        sx={{ borderRadius: 1 }}
      />
    </Box>
  );
};

GraphSkeleton.propTypes = {
  isCollapsed: PropTypes.bool,
};

export default GraphSkeleton;
