import React from "react";
import { styled } from "@mui/system";
import Box from "@mui/material/Box";
import { grey, action } from "src/theme/palette";

export const StyledBox = styled(Box)({
  color: "darkslategray",
  backgroundColor: "action.hover",
  borderRadius: 8,
  overflow: "hidden",
  border: `1px solid ${action.hover}`,
  "&.MuiBox-root": {
    "& .MuiFormControl-root": {
      "& .MuiInputBase-root": {
        "&.MuiFilledInput-root": {
          borderRadius: "0",
          padding: "12px 18px",
          "& .MuiInputBase-input": {
            color: grey[500],
          },
        },
      },
    },
  },
});
