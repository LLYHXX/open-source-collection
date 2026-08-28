import React from "react";
import { Skeleton, Grid, Box, Paper } from "@mui/material";

const SkeletonEvaluationCardsGrid = () => {
  const skeletonArray = Array.from({ length: 12 });

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Grid container spacing={2}>
        {skeletonArray.map((_, index) => (
          <Grid item xs={12} sm={6} md={4} key={index}>
            <Paper
              elevation={3}
              sx={{
                height: "114px",
                borderRadius: "4px",
                padding: "12px 16px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <Box>
                <Skeleton variant="text" width="60%" height={20} />
                <Skeleton variant="text" width="90%" height={18} />
              </Box>
              <Box sx={{ mt: 1, display: "flex", gap: 1 }}>
                <Skeleton variant="rounded" width={80} height={24} />
                <Skeleton variant="rounded" width={80} height={24} />
                <Skeleton variant="rounded" width={80} height={24} />
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default SkeletonEvaluationCardsGrid;
