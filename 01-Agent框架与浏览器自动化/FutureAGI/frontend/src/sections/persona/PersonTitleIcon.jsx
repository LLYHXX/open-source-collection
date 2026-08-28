import { Box } from "@mui/material";
import React from "react";
import SvgColor from "src/components/svg-color";

const PersonTitleIcon = () => {
  return (
    <Box
      sx={{
        width: "30px",
        height: "30px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "action.hover",
        borderRadius: "50%",
        flexShrink: 0,
      }}
    >
      <SvgColor
        src="/assets/icons/custom/persona.svg"
        sx={{ width: "15px", height: "15px" }}
      />
    </Box>
  );
};

export default PersonTitleIcon;
