import { Box, Skeleton, useTheme } from "@mui/material";
import React from "react";

const PerformanceCardSkeleton = () => (
  <Box
    sx={{
      backgroundColor: "background.default",
      borderRadius: 1,
      display: "flex",
      flexDirection: "column",
      flex: 1,
      padding: 2,
      paddingY: 1.5,
      justifyContent: "center",
      alignItems: "center",
      gap: 0.5,
    }}
  >
    <Skeleton variant="circular" width={20} height={20} />
    <Skeleton variant="text" width={60} height={24} />
    <Skeleton variant="text" width={80} height={16} />
  </Box>
);

const ScenarioCardSkeleton = () => (
  <Box
    sx={{
      backgroundColor: "background.default",
      borderRadius: 1,
      display: "flex",
      paddingX: 2,
      paddingY: 1,
      alignItems: "center",
      justifyContent: "space-between",
    }}
  >
    <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
      <Skeleton variant="text" width={120} height={20} />
      <Skeleton variant="text" width={80} height={16} />
    </Box>
    <Skeleton
      variant="rectangular"
      width={40}
      height={24}
      sx={{ borderRadius: 1 }}
    />
  </Box>
);

const PerformanceSkeleton = () => {
  const theme = useTheme();
  return (
    <Box
      sx={{
        border: "1px solid",
        borderColor: "divider",
        padding: 2,
        borderRadius: 1,
        gap: 1.5,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Test Run Performance Metrics Section */}
      <Skeleton variant="text" width={200} height={20} />

      {/* Performance Cards */}
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
        <PerformanceCardSkeleton theme={theme} />
        <PerformanceCardSkeleton theme={theme} />
        <PerformanceCardSkeleton theme={theme} />
      </Box>

      {/* Top Performing Scenarios Section */}
      <Skeleton variant="text" width={180} height={20} />

      {/* Scenarios Grid */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gap: "1px",
        }}
      >
        {Array.from({ length: 6 }).map((_, index) => (
          <ScenarioCardSkeleton key={index} theme={theme} />
        ))}
      </Box>
    </Box>
  );
};

export default PerformanceSkeleton;
