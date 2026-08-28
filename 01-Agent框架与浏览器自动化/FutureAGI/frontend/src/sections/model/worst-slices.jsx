import React from "react";
import { Stack, useTheme } from "@mui/material";

const NAV_WIDTH = 320;

export default function WorstSlices() {
  const theme = useTheme();

  return (
    <>
      <Stack
        sx={{
          height: 1,
          flexShrink: 0,
          width: NAV_WIDTH,
          borderRight: `solid 1px ${theme.palette.divider}`,
          transition: theme.transitions.create(["width"], {
            duration: theme.transitions.duration.shorter,
          }),
        }}
      >
        {/* {renderContent} */}
      </Stack>
    </>
  );
}
