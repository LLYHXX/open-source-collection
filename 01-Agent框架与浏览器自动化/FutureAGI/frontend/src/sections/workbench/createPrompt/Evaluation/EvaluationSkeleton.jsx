import { Box, Skeleton, useTheme } from "@mui/material";
import React from "react";

const EvaluationSkeleton = () => {
  const theme = useTheme();
  return (
    <Box
      height={"100%"}
      alignItems={"center"}
      display={"flex"}
      paddingLeft={theme.spacing(2)}
    >
      <Skeleton
        sx={{
          bgcolor: "background.neutral",
          borderRadius: theme.spacing(0.5),
        }}
        width={"70%"}
      />
    </Box>
  );
};

export default EvaluationSkeleton;
