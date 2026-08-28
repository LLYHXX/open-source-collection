import { Box, Skeleton, Stack } from "@mui/material";
import React from "react";

export default function AgentNodeFormSkeleton() {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {/* Agent dropdown */}
      <Stack gap={0.75}>
        <Skeleton variant="text" width={40} height={20} />
        <Skeleton variant="rounded" height={40} />
      </Stack>

      {/* Version dropdown */}
      <Stack gap={0.75}>
        <Skeleton variant="text" width={55} height={20} />
        <Skeleton variant="rounded" height={40} />
      </Stack>

      {/* Graph preview area */}
      <Skeleton variant="rounded" height={160} />

      {/* Save button */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-end",
          pt: 1.5,
          borderTop: 1,
          borderColor: "divider",
        }}
      >
        <Skeleton variant="rounded" width={60} height={32} />
      </Box>
    </Box>
  );
}
