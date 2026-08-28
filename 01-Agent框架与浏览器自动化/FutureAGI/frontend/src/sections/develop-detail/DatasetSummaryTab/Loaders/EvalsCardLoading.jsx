import { Box, Skeleton } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const EvalsCardLoading = ({ isCompare }) => {
  return (
    <Box display={"flex"} gap={2} flexDirection={"column"} height="97%">
      {isCompare ? (
        <Box>
          <Skeleton animation="pulse" height={300} />
        </Box>
      ) : (
        <Box display={"flex"} gap={2} flexWrap={"wrap"}>
          <Box sx={{ width: "calc(65% - 8px)" }}>
            <Skeleton animation="pulse" height={300} />
          </Box>
          <Box sx={{ width: "calc(35% - 8px)" }}>
            <Skeleton animation="pulse" height={300} />
          </Box>
        </Box>
      )}
      <Box display={"flex"} gap={2} flexWrap={"wrap"}>
        <Box sx={{ width: "calc(50% - 8px)" }}>
          <Skeleton animation="pulse" height={300} />
        </Box>
        <Box sx={{ width: "calc(50% - 8px)" }}>
          <Skeleton animation="pulse" height={300} />
        </Box>
      </Box>
      <Box display={"flex"} gap={2} flexWrap={"wrap"}>
        <Box sx={{ width: "calc(50% - 8px)" }}>
          <Skeleton animation="pulse" height={300} />
        </Box>
        <Box sx={{ width: "calc(50% - 8px)" }}>
          <Skeleton animation="pulse" height={300} />
        </Box>
      </Box>
    </Box>
  );
};

export default EvalsCardLoading;

EvalsCardLoading.propTypes = {
  isCompare: PropTypes.bool,
};
