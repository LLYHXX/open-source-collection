import { Box, Skeleton } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const PromptCardLoading = ({ isCompare }) => {
  return (
    <Box display={"flex"} gap={2} flexDirection={"column"} height="97%">
      {isCompare ? (
        <Box display={"flex"} gap={2} justifyContent="space-between">
          <Box sx={{ flex: 1 }}>
            <Skeleton animation="pulse" height={60} variant="rectangular" />
            <Skeleton animation="pulse" height={30} variant="rectangular" />
            <Skeleton animation="pulse" height={30} variant="rectangular" />
            <Skeleton animation="pulse" height={30} variant="rectangular" />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Skeleton animation="pulse" height={60} variant="rectangular" />
            <Skeleton animation="pulse" height={30} variant="rectangular" />
            <Skeleton animation="pulse" height={30} variant="rectangular" />
            <Skeleton animation="pulse" height={30} variant="rectangular" />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Skeleton animation="pulse" height={60} variant="rectangular" />
            <Skeleton animation="pulse" height={30} variant="rectangular" />
            <Skeleton animation="pulse" height={30} variant="rectangular" />
            <Skeleton animation="pulse" height={30} variant="rectangular" />
          </Box>
        </Box>
      ) : (
        <Box display={"flex"} gap={2} justifyContent="space-between">
          <Box sx={{ flex: 1 }}>
            <Skeleton animation="pulse" height={100} variant="rectangular" />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Skeleton animation="pulse" height={100} variant="rectangular" />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Skeleton animation="pulse" height={100} variant="rectangular" />
          </Box>
        </Box>
      )}
      <Skeleton animation="pulse" height={30} variant="rectangular" />
      <Skeleton animation="pulse" height={400} variant="rectangular" />
    </Box>
  );
};

export default PromptCardLoading;

PromptCardLoading.propTypes = {
  isCompare: PropTypes.bool,
};
