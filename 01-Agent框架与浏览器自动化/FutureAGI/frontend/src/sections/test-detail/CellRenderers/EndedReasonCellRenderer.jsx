import { Typography } from "@mui/material";
import React from "react";

const EndedReasonCellRenderer = (params) => {
  return (
    <Typography
      typography={"s2"}
      fontWeight={"fontWeightRegular"}
      sx={{
        padding: "8px 4px",
        lineHeight: 1.5,
        whiteSpace: "normal",
        wordBreak: "break-word",
      }}
    >
      {params.data?.ended_reason || "-"}
    </Typography>
  );
};

export default EndedReasonCellRenderer;
