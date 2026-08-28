import { Box, Grid, Skeleton } from "@mui/material";
import React from "react";

export default function EvalsCardSkeleton() {
  return (
    <>
      <Box
        sx={{ overflowY: "hidden", width: "100%", marginBottom: "20px" }}
        gap={5}
      >
        <Skeleton
          variant="rectangular"
          width="100%"
          height={300}
          animation="wave"
        />
      </Box>
      <Box sx={{ overflowY: "hidden", width: "100%", marginBottom: "48px" }}>
        <Skeleton
          variant="rectangular"
          width="100%"
          height={300}
          animation="wave"
        />
      </Box>
      <Grid
        container
        sx={{
          borderTop: 3,
          borderTopStyle: "solid",
          borderTopColor: "divider",
        }}
      >
        <Grid item sm={3}>
          <Box
            sx={{
              px: "12px",
              py: "17px",
              borderRight: 3,
              borderRightStyle: "solid",
              borderRightColor: "divider",
              height: "100%",
            }}
          >
            <Skeleton variant="rectangular" width="100%" height={200} />
          </Box>
        </Grid>
        <Grid item sm={9}>
          <Box sx={{ pl: { sm: "44px" }, pt: "24px" }}>
            <Skeleton variant="text" width="60%" height={40} />
            <Skeleton variant="text" width="40%" height={30} />
            <Skeleton variant="rectangular" width="100%" height={350} />
          </Box>
        </Grid>
      </Grid>
    </>
  );
}
