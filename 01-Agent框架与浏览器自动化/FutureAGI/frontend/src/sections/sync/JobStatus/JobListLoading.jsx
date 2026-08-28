import { Box, Skeleton, TableCell, TableRow } from "@mui/material";
import React from "react";

const JobListLoading = () => {
  return (
    <>
      {[...Array(10)].map((i) => (
        <TableRow key={i}>
          <TableCell>
            <Skeleton width={128} />
          </TableCell>
          <TableCell>
            <Skeleton width={128} />
          </TableCell>
          <TableCell>
            <Skeleton width={128} />
          </TableCell>
          <TableCell>
            <Box sx={{ display: "flex", justifyContent: "center" }}>
              <Skeleton width={128} />
            </Box>
          </TableCell>
        </TableRow>
      ))}
    </>
  );
};

export default JobListLoading;
