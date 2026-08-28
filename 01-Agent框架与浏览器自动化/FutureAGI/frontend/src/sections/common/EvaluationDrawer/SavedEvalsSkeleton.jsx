import React from "react";
import { Box, Skeleton } from "@mui/material";

const SavedEvalsSkeleton = () => {
  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      gap={2}
    >
      {[...Array(3)].map((_, index) => (
        <Box
          key={index}
          py={2}
          px={1.5}
          height="116px"
          border="1px solid"
          borderColor="divider"
          borderRadius={1}
        >
          <Skeleton variant="text" width="50%" height={24} />
          <Skeleton variant="text" width="80%" height={24} />
          <Box display="flex" gap={1} mt={1}>
            <Skeleton variant="rounded" width={120} height={24} />
            <Skeleton variant="rounded" width={150} height={24} />
          </Box>
        </Box>
      ))}
    </Box>
  );
};

export default SavedEvalsSkeleton;
