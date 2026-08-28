import { Box, Skeleton } from "@mui/material";
import React from "react";

const TestRunInsightSkeletonCard = () => {
  return (
    <Box
      sx={{
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        display: "inline-flex",
        padding: 2,
        backgroundColor: "background.paper",
        minWidth: "200px",
        flex: 1,
        flexDirection: "column",
      }}
    >
      <Box sx={{ display: "flex", gap: 1, alignItems: "baseline" }}>
        <Skeleton variant="text" width={60} height={32} />
      </Box>
      <Skeleton variant="text" width={120} height={20} sx={{ mt: 1 }} />
    </Box>
  );
};

export default TestRunInsightSkeletonCard;
