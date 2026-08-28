import { Box, Stack, Typography } from "@mui/material";
import React from "react";
import { typography } from "src/theme/typography";

export default function NoDataSetUi() {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "400px",
      }}
    >
      <img
        style={{
          height: "109px",
          width: "117px",
        }}
        alt="no dataset added ui"
        src="/assets/illustrations/no-dataset-added.svg"
      />
      <Stack direction={"column"} rowGap={0} alignItems={"center"}>
        <Typography
          sx={{
            mt: 2.5,
            mb: 2,
            fontFamily: typography.fontFamily,
            color: "text.primary",
            ...typography.subtitle2,
          }}
        >
          No Datasets added
        </Typography>
        <Typography
          sx={{
            fontFamily: typography.fontFamily,
            color: "text.disabled",
            fontWeight: typography.fontWeightRegular,
            ...typography.s1,
          }}
        >
          Add and work with datasets by clicking on add dataset button
        </Typography>
      </Stack>
    </Box>
  );
}
