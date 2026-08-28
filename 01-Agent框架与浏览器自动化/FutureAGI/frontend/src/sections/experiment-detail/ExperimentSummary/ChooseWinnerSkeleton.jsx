import { Box, Skeleton, Typography } from "@mui/material";
import React from "react";

const ChooseWinnerSkeleton = () => {
  return (
    <>
      <Box
        role="progressbar"
        aria-label="Loading experiment comparison data"
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
          height: "100%",
          justifyContent: "space-between",
        }}
      >
        <Box sx={{ flex: 1 }}>
          <Box>
            <Typography
              variant="body2"
              fontWeight={400}
              sx={{
                paddingBottom: "10px",
                display: "flex",
                justifyContent: "space-between",
              }}
            >
              <Skeleton width={200} />
              <Skeleton width={20} height={20} variant="rectangular" />
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ paddingTop: 3 }}
            >
              <Skeleton />
            </Typography>
          </Box>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              flexWrap: "wrap",
              paddingTop: 8,
              gap: 5,
            }}
          >
            {[0, 1, 2, 3].map((tag) => (
              <Box key={tag}>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: "10px",
                    alignItems: "center",
                  }}
                >
                  <Typography variant="body2" fontWeight={400}>
                    <Skeleton width={200} height={15} />
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    <Skeleton width={80} height={30} variant="rectangular" />
                  </Typography>
                </Box>
                <Skeleton key={tag} variant="rounded" height={8} />
              </Box>
            ))}
          </Box>
        </Box>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            marginBottom: "10px",
            // backgroundColor: "rgba(0, 0, 0,1)",
          }}
        >
          <Typography variant="body2" fontWeight={400}>
            <Skeleton width={250} height={20} />
          </Typography>
          <Typography variant="body2" fontWeight={400}>
            <Skeleton width={250} height={20} />
          </Typography>
        </Box>
      </Box>
    </>
  );
};

export default ChooseWinnerSkeleton;
