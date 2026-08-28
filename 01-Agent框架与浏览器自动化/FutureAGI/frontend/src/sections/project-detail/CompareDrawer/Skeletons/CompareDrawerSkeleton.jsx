import { Box, Skeleton, styled } from "@mui/material";
import React from "react";

const Section = styled(Box)(({ theme }) => ({
  border: "1px solid",
  borderColor: theme.palette.background.neutral,
  borderLeft: "0px",
  borderRight: "0px",
  borderBottom: "0px",
  padding: "8px",
}));

const CompareDrawerSkeleton = () => {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 2,
        height: "100%",
        width: "100%",
      }}
    >
      <Box sx={{ paddingX: 2 }}>
        <Skeleton
          variant="rectangular"
          height="25px"
          width="100px"
          sx={{ borderRadius: 1 }}
        />
      </Box>
      <Box
        sx={{
          display: "flex",
          flex: 1,
          width: "100%",
        }}
      >
        {Array.from({ length: 3 }).map((_, index) => (
          <Box
            key={index}
            sx={{
              width: "33.33vw",
              borderRight: index < 2 ? "1px solid" : "none", // Avoid last border
              borderColor: "background.neutral",
              flexShrink: 0,
              boxSizing: "border-box",
              padding: 2,
            }}
          >
            <Section>
              <Skeleton
                variant="rectangular"
                height="20px"
                width="180px"
                sx={{ borderRadius: 1 }}
              />
            </Section>
            <Section sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <Skeleton
                variant="rectangular"
                height="20px"
                width="200px"
                sx={{ borderRadius: 1, marginBottom: 1 }}
              />
              <Skeleton
                variant="rectangular"
                height="22px"
                width="130px"
                sx={{ borderRadius: 1 }}
              />
              <Skeleton
                variant="rectangular"
                height="22px"
                width="200px"
                sx={{ borderRadius: 1 }}
              />
              <Skeleton
                variant="rectangular"
                height="22px"
                width="160px"
                sx={{ borderRadius: 1 }}
              />
            </Section>
            <Section sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <Skeleton
                  variant="rectangular"
                  height="20px"
                  width="200px"
                  sx={{ borderRadius: 1 }}
                />
                <Box sx={{ display: "flex", gap: 1 }}>
                  <Skeleton
                    variant="rectangular"
                    height="20px"
                    width="20px"
                    sx={{ borderRadius: 1 }}
                  />
                  <Skeleton
                    variant="rectangular"
                    height="20px"
                    width="20px"
                    sx={{ borderRadius: 1 }}
                  />
                </Box>
              </Box>
              {[...Array(4)].map((_, i) => (
                <Skeleton
                  key={i}
                  variant="rectangular"
                  height="150px"
                  width="100%"
                  sx={{ borderRadius: 1 }}
                />
              ))}
            </Section>
          </Box>
        ))}
      </Box>
    </Box>
  );
};

export default CompareDrawerSkeleton;
