import { Box, Typography } from "@mui/material";
import React from "react";

const NoJobQuery = () => {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        height: "100%",
        width: "100%",
      }}
    >
      <Box
        component="img"
        alt="empty content"
        src={"/assets/icons/components/ic_extra_scroll.svg"}
        sx={{ width: 1, maxWidth: 160 }}
      />
      <Typography
        variant="subtitle1"
        sx={{ width: "250px", textAlign: "center" }}
      >
        No Queries Found
      </Typography>
    </Box>
  );
};

export default NoJobQuery;
