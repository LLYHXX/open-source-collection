import { Box, Skeleton, Stack } from "@mui/material";
import React from "react";

export default function NodeDrawerSkeleton() {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2, py: 1 }}>
      {/* Label field */}
      <Stack gap={0.75}>
        <Skeleton variant="rounded" height={40} />
      </Stack>

      {/* Second field */}
      <Stack gap={0.75}>
        <Skeleton variant="text" width={70} height={20} />
        <Skeleton variant="rounded" height={40} />
      </Stack>

      {/* Content area */}
      <Skeleton variant="rounded" height={120} />

      {/* Another field */}
      <Stack gap={0.75}>
        <Skeleton variant="text" width={90} height={20} />
        <Skeleton variant="rounded" height={40} />
      </Stack>

      {/* Bottom area */}
      <Skeleton variant="rounded" height={80} />

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
