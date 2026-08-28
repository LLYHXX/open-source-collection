import React from "react";
import { Box, Skeleton, Stack } from "@mui/material";
import PropTypes from "prop-types";

export const AlertTableSkeleton = () => {
  return (
    <Box
      sx={{
        p: 3,
      }}
    >
      <Stack direction={"row"} justifyContent={"space-between"}>
        <Skeleton
          animation="wave"
          variant="text"
          height={40}
          width="30%"
          sx={{ mb: 2 }}
        />
        <Stack direction={"row"} gap={2}>
          <Skeleton
            animation="wave"
            variant="text"
            height={40}
            width="40px"
            sx={{ mb: 2 }}
          />
          <Skeleton
            animation="wave"
            variant="text"
            height={40}
            width="40px"
            sx={{ mb: 2 }}
          />
          <Skeleton
            animation="wave"
            variant="text"
            height={40}
            width="100px"
            sx={{ mb: 2 }}
          />
        </Stack>
      </Stack>
      <Skeleton
        animation="wave"
        variant="rounded"
        width={"100%"}
        height={"400px"}
      />
    </Box>
  );
};

export const EmptyAlertsSkeleton = ({ mainPage }) => {
  return (
    <Stack
      sx={{
        p: 3,
        width: "100%",
        height: "90vh",
        overflow: "hidden",
        justifyContent: "center",
        alignItems: mainPage ? "center" : "flex-start",
        gap: 2,
      }}
    >
      <Stack
        direction={"column"}
        justifyContent={"center"}
        alignItems={"center"}
      >
        <Skeleton animation="wave" variant="text" height={40} width="200px" />
        <Skeleton animation="wave" variant="text" height={40} width="400px" />
      </Stack>
      <Stack direction={"row"} gap={3}>
        <Skeleton height={300} width={300} />
        <Skeleton height={300} width={300} />
        <Skeleton height={300} width={300} />
      </Stack>
    </Stack>
  );
};

EmptyAlertsSkeleton.propTypes = {
  mainPage: PropTypes.bool,
};

export const SelectAlertTypeSkeleton = () => {
  return (
    <Stack direction={"row"} gap={2}>
      <Skeleton
        animation="wave"
        variant="rounded"
        width={"100%"}
        height={"60vh"}
      />
      <Skeleton
        animation="wave"
        variant="rounded"
        width={"100%"}
        height={"60vh"}
      />
    </Stack>
  );
};

export const AlertConfigFormSkeleton = () => {
  return (
    <Stack direction={"column"} gap={2}>
      <Skeleton
        animation="wave"
        variant="rounded"
        width={"100%"}
        height={300}
      />
      <Skeleton
        animation="wave"
        variant="rounded"
        width={"100%"}
        height={300}
      />
    </Stack>
  );
};
