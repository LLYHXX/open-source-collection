import { Box, Skeleton, Typography } from "@mui/material";
import React from "react";

const EvalTypesSkeleton = () => {
  return (
    <>
      {[0, 1, 2, 3].map((k) => (
        <Box
          key={k}
          sx={{
            paddingY: "15px",
            paddingX: "18px",
            display: "flex",
            flexDirection: "column",
            gap: 1,
            border: "1px solid",
            borderColor: "divider",
            borderRadius: 1,
            cursor: "pointer",
          }}
        >
          <Typography variant="body2" fontWeight={400}>
            <Skeleton width={200} />
          </Typography>
          <Typography variant="caption" color="text.secondary">
            <Skeleton />
          </Typography>
          <Box
            sx={{ display: "flex", gap: 1, flexWrap: "wrap", paddingTop: 3 }}
          >
            {[0, 1].map((tag) => (
              <Skeleton key={tag} variant="rounded" width={100} height={20} />
            ))}
          </Box>
        </Box>
      ))}
    </>
  );
};

export default EvalTypesSkeleton;
