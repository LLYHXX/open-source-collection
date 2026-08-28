import { Box, Typography } from "@mui/material";
import React, { useEffect } from "react";
import { useXarrow } from "react-xarrows";

export const UsersNoData = () => {
  const updateXarrow = useXarrow();

  useEffect(() => {
    updateXarrow();
  });

  return (
    <Box
      sx={{
        minHeight: "714px",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        position: "relative",
      }}
    >
      <Box
        sx={{ display: "flex", flexDirection: "column", alignItems: "center" }}
      >
        <Box
          component="img"
          alt="empty content"
          src={"/assets/icons/components/ic_extra_scroll.svg"} // Ensure this path is correct
          sx={{ width: 1, maxWidth: 160 }}
        />
        <Typography
          variant="subtitle1"
          sx={{ width: "250px", textAlign: "center" }}
          id="no-users-text"
        >
          No data found.
        </Typography>
      </Box>
    </Box>
  );
};

export default UsersNoData;
