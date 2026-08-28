import { Box, TableCell, TableRow, Typography } from "@mui/material";
import React from "react";

const NoJobList = () => {
  return (
    <TableRow>
      <TableCell colSpan={4}>
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            height: "100%",
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
            No connection found
          </Typography>
        </Box>
      </TableCell>
    </TableRow>
  );
};

export default NoJobList;
