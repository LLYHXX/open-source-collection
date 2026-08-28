import { Box, Divider, Skeleton } from "@mui/material";
import React from "react";
import EvaluationMappingFormSkeleton from "src/sections/common/EvaluationDrawer/EvaluationMappingFormSkeleton";

const EvalsConfigLoading = () => {
  return (
    <Box display={"flex"} gap={2} paddingTop={1} height="100%">
      <Box display={"flex"} gap={1} flexDirection={"column"} width={"100%"}>
        <Skeleton width={"200px"} height={"20px"} />
        <Skeleton width={"70%"} height={"16px"} />
        <Skeleton width={"100%"} height={"60px"} />
        <Skeleton width={"100%"} height={"60px"} />
        <Skeleton width={"100%"} height={"200px"} />
        <Skeleton width={"100%"} height={"80px"} />
        <Skeleton width={"100%"} height={"200px"} />
      </Box>
      <Divider orientation="vertical" />
      <EvaluationMappingFormSkeleton />
    </Box>
  );
};

export default EvalsConfigLoading;
