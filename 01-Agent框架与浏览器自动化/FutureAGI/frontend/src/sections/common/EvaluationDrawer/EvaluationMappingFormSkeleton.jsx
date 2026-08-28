import { Box, Skeleton } from "@mui/material";
import React from "react";

const EvaluationMappingFormSkeleton = () => {
  return (
    <Box display={"flex"} gap={1} flexDirection={"column"} width={"100%"}>
      <Skeleton width={"200px"} height={"20px"} />
      <Skeleton width={"80%"} height={"16px"} />
      <Skeleton width={"100%"} height={"50px"} />
      <Skeleton width={"100%"} height={"200px"} />
      <Skeleton width={"100%"} height={"80px"} />
    </Box>
  );
};

export default EvaluationMappingFormSkeleton;
