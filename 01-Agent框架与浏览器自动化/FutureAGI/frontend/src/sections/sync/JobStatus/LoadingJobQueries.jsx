import { Box, Skeleton } from "@mui/material";
import React from "react";

const LoadingJobQueries = () => {
  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", gap: 1.5, paddingTop: 2 }}
    >
      <Skeleton width="100%" height={50} />
      <Skeleton width="100%" height={50} />
      <Skeleton width="100%" height={50} />
      <Skeleton width="100%" height={50} />
      <Skeleton width="100%" height={50} />
    </Box>
  );
};

export default LoadingJobQueries;
