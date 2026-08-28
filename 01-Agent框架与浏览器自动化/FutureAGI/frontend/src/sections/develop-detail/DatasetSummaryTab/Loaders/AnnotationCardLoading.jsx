import { Box, Skeleton } from "@mui/material";
import React from "react";

const AnnotationCardLoading = () => {
  return (
    <Box display={"flex"} gap={2} flexDirection={"column"} height="97%">
      <Box display={"flex"} gap={2}>
        <Box sx={{ flex: 1 }}>
          <Skeleton animation="pulse" height={150} />
        </Box>
        <Box sx={{ flex: 1 }}>
          <Skeleton animation="pulse" height={150} />
        </Box>
        <Box sx={{ flex: 1 }}>
          <Skeleton animation="pulse" height={150} />
        </Box>
      </Box>

      <Box display={"flex"} gap={2} flexWrap={"wrap"}>
        <Box sx={{ width: "calc(50% - 8px)" }}>
          <Skeleton animation="pulse" height={350} />
        </Box>
        <Box sx={{ width: "calc(50% - 8px)" }}>
          <Skeleton animation="pulse" height={350} />
        </Box>
      </Box>
      <Box display={"flex"} gap={2} flexWrap={"wrap"}>
        <Box sx={{ width: "calc(50% - 8px)" }}>
          <Skeleton animation="pulse" height={350} />
        </Box>
        <Box sx={{ width: "calc(50% - 8px)" }}>
          <Skeleton animation="pulse" height={350} />
        </Box>
      </Box>

      <Box display={"flex"} gap={2} flexWrap={"wrap"}>
        <Box sx={{ width: "calc(50% - 8px)" }}>
          <Skeleton animation="pulse" height={350} />
        </Box>
      </Box>

      <Box display={"flex"} gap={2}>
        <Box sx={{ flex: 1 }}>
          <Skeleton animation="pulse" height={220} />
        </Box>
        <Box sx={{ flex: 1 }}>
          <Skeleton animation="pulse" height={220} />
        </Box>
        <Box sx={{ flex: 1 }}>
          <Skeleton animation="pulse" height={220} />
        </Box>
      </Box>
    </Box>
  );
};

export default AnnotationCardLoading;
