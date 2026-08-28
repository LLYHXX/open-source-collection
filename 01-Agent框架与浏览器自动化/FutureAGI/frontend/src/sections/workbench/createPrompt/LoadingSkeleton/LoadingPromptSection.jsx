import { Box, Skeleton, useTheme } from "@mui/material";
import React from "react";

const LoadingPromptSection = () => {
  const theme = useTheme();
  return (
    <Box
      sx={{
        display: "flex",
        gap: theme.spacing(2),
        flexDirection: "column",
        height: "100%",
      }}
    >
      <Box sx={{ display: "flex", gap: theme.spacing(1.5) }}>
        <Skeleton
          variant="rectangular"
          sx={{ borderRadius: "4px" }}
          height={24}
          width={100}
        />
        <Skeleton
          variant="rectangular"
          sx={{ borderRadius: "4px" }}
          height={24}
          width={24}
        />
        <Skeleton
          variant="rectangular"
          sx={{ borderRadius: "4px" }}
          height={24}
          width={24}
        />
      </Box>
      <Box
        sx={{
          display: "flex",
          gap: theme.spacing(2),
          flexDirection: "column",
          overflowY: "auto",
          height: "100%",
        }}
      >
        <Skeleton
          variant="rectangular"
          sx={{ borderRadius: "4px" }}
          height={80}
        />
        <Skeleton
          variant="rectangular"
          sx={{ borderRadius: "4px" }}
          height={80}
        />
        <Box sx={{ display: "flex", gap: theme.spacing(1) }}>
          <Skeleton
            variant="rectangular"
            sx={{ borderRadius: "4px" }}
            width={150}
            height={30}
          />
          <Skeleton
            variant="rectangular"
            sx={{ borderRadius: "4px" }}
            width={150}
            height={30}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default LoadingPromptSection;
