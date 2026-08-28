import { Box, Skeleton, Typography } from "@mui/material";
import React from "react";

const AnnotationsModalSkeleton = () => {
  return (
    <Box padding={2}>
      <Box padding={"0px 0px 0px 15px"}>
        <Skeleton variant="rounded" width={"50%"} height={20} />
        <Box padding={"20px 0px 0px"}>
          <Skeleton variant="rounded" width={"50%"} height={20} />
        </Box>
      </Box>
      <Box padding={"20px 5px 30px"}>
        {[0, 1, 2, 3, 4].map((k) => (
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
            margin={1}
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
              <Skeleton variant="rounded" width={100} height={20} />
            </Box>
          </Box>
        ))}
      </Box>
    </Box>
  );
};

export default AnnotationsModalSkeleton;
