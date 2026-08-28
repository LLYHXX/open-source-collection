import { Box, Skeleton, Stack } from "@mui/material";
import React from "react";

const SkeltonForTestDeatilDrawer = () => {
  return (
    <Stack spacing={2} width={"90vw"} padding={2}>
      <Box display={"flex"} flexDirection={"column"} gap={1}>
        <Skeleton width={"200px"} height={"20px"} />
        <Skeleton width={"400px"} height={"20px"} />
        <Skeleton width={"300px"} height={"20px"} />
      </Box>
      <Skeleton width={"100%"} height={"250px"} />
      <Skeleton width={"100%"} height={"250px"} />
      <Box
        sx={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          gap: 2,
        }}
      >
        <Skeleton width={"50%"} height={"350px"} />
        <Skeleton width={"50%"} height={"350px"} />
      </Box>
    </Stack>
  );
};

export default SkeltonForTestDeatilDrawer;
