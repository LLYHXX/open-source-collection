import React from "react";
import Typography from "@mui/material/Typography";

const ComingSoon = () => {
  return (
    <>
      <Typography
        variant="subtitle1"
        sx={{
          fontWeight: "subtitle1",
          textAlign: "left",
          marginBottom: "20px",
          color: "text.disabled",
        }}
      >
        Coming Soon...
      </Typography>
    </>
  );
};

export default ComingSoon;
