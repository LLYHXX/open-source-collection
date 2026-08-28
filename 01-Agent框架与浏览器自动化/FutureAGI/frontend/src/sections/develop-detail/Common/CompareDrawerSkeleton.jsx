import { Box, Skeleton } from "@mui/material";
import React from "react";

const CompareDrawerSkeleton = () => {
  return (
    <Box sx={{ flexGrow: 1, paddingX: 0.5, overflowY: "auto" }}>
      {[1, 2, 3, 4, 5, 6, 7].map((k) => (
        <Box
          key={k}
          sx={{
            padding: 1,
            borderColor: "divider",
            cursor: "pointer",
          }}
        >
          <Skeleton
            variant="rounded"
            height={"32px"}
            sx={{ borderRadius: "4px" }}
            width={"100%"}
          />
        </Box>
      ))}
    </Box>
  );
};

export default CompareDrawerSkeleton;
