import { Box, Skeleton, useTheme } from "@mui/material";
import React from "react";

const LoadingPromptAction = () => {
  const theme = useTheme();
  return (
    <Box display="flex" gap={theme.spacing(0.5)} flexDirection={"column"}>
      <Box>
        <Skeleton
          variant="rectangular"
          sx={{ borderRadius: "4px" }}
          height={22}
          width={186}
        />
      </Box>
      <Box>
        <Skeleton
          variant="rectangular"
          sx={{ borderRadius: "4px" }}
          height={16}
          width={213}
        />
      </Box>
      <Box>
        <Skeleton
          variant="rectangular"
          sx={{ borderRadius: "4px" }}
          height={16}
          width={213}
        />
      </Box>
    </Box>
  );
};

export default LoadingPromptAction;
