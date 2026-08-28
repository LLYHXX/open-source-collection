import { Box, Skeleton } from "@mui/material";
import React from "react";

const VersionCardSkeleton = () => {
  return (
    <Box
      sx={{
        border: "1px solid",
        borderColor: "divider",
        padding: 2,
        borderRadius: 1,
        gap: "4px",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Skeleton variant="rectangular" width={125} height={22} />
      <Skeleton variant="rectangular" width={144} height={16} />
      <Skeleton variant="rectangular" width={168} height={24} />
      <Skeleton variant="rectangular" width="100%" height={20} />
    </Box>
  );
};

export default VersionCardSkeleton;
