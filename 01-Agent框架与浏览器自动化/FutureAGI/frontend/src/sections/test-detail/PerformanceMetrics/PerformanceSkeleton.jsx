import React from "react";
import { Box, Grid, Skeleton, Typography, Card } from "@mui/material";

const PerformanceSkeleton = () => {
  return (
    <Grid container spacing={2}>
      {/* --- CALL DETAILS --- */}
      <Grid item xs={12} md={2}>
        <Card sx={{ p: 2, borderRadius: 2 }}>
          <Typography
            typography="s2_1"
            color="text.primary"
            fontWeight={"fontWeightMedium"}
          >
            CALL DETAILS
          </Typography>

          <Box sx={{ display: "flex", alignItems: "center", gap: 2, my: 2 }}>
            <Skeleton variant="circular" width={40} height={40} />
            <Box>
              <Skeleton width={30} height={24} />
              <Skeleton width={100} height={16} />
            </Box>
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <Skeleton variant="circular" width={40} height={40} />
            <Box>
              <Skeleton width={30} height={24} />
              <Skeleton width={100} height={16} />
            </Box>
          </Box>
        </Card>
      </Grid>

      {/* --- SYSTEM METRICS --- */}
      <Grid item xs={12} md={4}>
        <Card sx={{ p: 2, borderRadius: 2 }}>
          <Typography
            typography="s2_1"
            color="text.primary"
            fontWeight={"fontWeightMedium"}
          >
            SYSTEM METRICS
          </Typography>

          <Grid
            container
            spacing={2}
            sx={{
              my: 2,
            }}
          >
            {[...Array(4)].map((_, i) => (
              <Grid item xs={6} key={i}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Skeleton variant="rounded" width={40} height={40} />
                  <Box>
                    <Skeleton width={80} height={16} />
                    <Skeleton width={50} height={24} />
                  </Box>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Card>
      </Grid>

      {/* --- EVALUATION METRICS --- */}
      <Grid item xs={12} md={6}>
        <Card sx={{ p: 2, borderRadius: 2 }}>
          <Typography
            typography="s2_1"
            color="text.primary"
            fontWeight={"fontWeightMedium"}
          >
            EVALUATION METRICS
          </Typography>

          <Box
            sx={{
              my: 2,
            }}
          />
          {[...Array(3)].map((_, i) => (
            <Box key={i} sx={{ mb: 2 }}>
              <Skeleton width={120} height={16} sx={{ mb: 1 }} />
              <Skeleton variant="rectangular" height={10} width="100%" />
            </Box>
          ))}
        </Card>
      </Grid>
    </Grid>
  );
};

export default PerformanceSkeleton;
