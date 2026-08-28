import React from "react";
import { Box, Typography } from "@mui/material";

const NoVariables = () => {
  return (
    <Box
      sx={{
        padding: "10px 16px 0 16px",
        height: "calc(100% - 60px)",
        overflow: "auto",
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: "18px",
          justifyContent: "center",
          alignItems: "center",
          textAlign: "center",
          height: "100%",
          maxWidth: "455px",
          margin: "0 auto",
        }}
      >
        <Typography typography="body1" fontWeight="fontWeightBold">
          No Variables
        </Typography>
        <Typography typography="body2" lineHeight="22px" color="text.primary">
          Use variables to test the prompt across different scenarios. You can
          create a variable inline like this:
          <Typography
            color="primary.light"
            fontWeight="fontWeightBold"
            display="contents"
          >{`{{variable_name}}`}</Typography>
        </Typography>
      </Box>
    </Box>
  );
};

export default NoVariables;
