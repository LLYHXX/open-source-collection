import React from "react";
import { Box, Skeleton, Stack } from "@mui/material";

const AddedEvaluationsSkeleton = () => {
  return (
    <Stack gap={1.5}>
      {/* Header: "All Evals" + "Add Evaluations" button */}
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Skeleton variant="text" width={90} height={24} />
        <Skeleton
          variant="rounded"
          width={150}
          height={32}
          sx={{ borderRadius: "8px" }}
        />
      </Box>
      {/* Eval card */}
      <Box
        sx={{
          border: "1px solid",
          borderColor: "divider",
          borderRadius: 1,
          p: 1.5,
        }}
      >
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          mb={1}
        >
          <Skeleton variant="text" width="60%" height={22} />
          <Skeleton variant="rounded" width={28} height={28} />
        </Box>
        <Stack gap={0.5}>
          <Skeleton variant="text" width="50%" height={18} />
          <Skeleton variant="text" width="55%" height={18} />
        </Stack>
      </Box>
    </Stack>
  );
};

export default AddedEvaluationsSkeleton;
