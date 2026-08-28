import React from "react";
import { Stack, Typography } from "@mui/material";
import PropTypes from "prop-types";

const AgentNameCellRenderer = ({ data }) => {
  const name = data?.agentName;
  const description = data?.description || "";

  return (
    <Stack
      display={"flex"}
      direction={"column"}
      justifyContent={"center"}
      height="100%"
      spacing={0.25}
      width="100%"
    >
      <Typography
        variant="s1"
        fontWeight={"fontWeightMedium"}
        sx={{ color: "text.primary" }}
      >
        {name}
      </Typography>

      <Typography
        color="text.primary"
        fontWeight={"fontWeightRegular"}
        variant="s2_1"
        sx={{
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          width: "100%",
          display: "block",
        }}
      >
        {description}
      </Typography>
    </Stack>
  );
};

AgentNameCellRenderer.propTypes = {
  data: PropTypes.object,
};

export default AgentNameCellRenderer;
