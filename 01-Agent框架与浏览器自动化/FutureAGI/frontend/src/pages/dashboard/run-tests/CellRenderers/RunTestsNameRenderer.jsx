import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const RunTestsNameRenderer = ({ data }) => {
  const { name, description, scenarios } = data ?? {};
  const totalScenarios = scenarios.length;

  return (
    <Box
      display={"flex"}
      height={"100%"}
      flexDirection={"column"}
      justifyContent={"center"}
    >
      <Typography
        marginLeft={1.5}
        variant="s1"
        fontWeight={500}
        color="text.primary"
      >
        {name}
      </Typography>
      <Box
        display={"flex"}
        flexDirection={"row"}
        gap={1}
        marginLeft={1.5}
        alignItems={"center"}
      >
        {description && (
          <Typography variant="s2" fontWeight={500} color="text.secondary">
            {description}
          </Typography>
        )}
        <Typography variant="s3" fontWeight={500} color="text.secondary">
          {totalScenarios} {`scenario${totalScenarios > 1 ? "s" : ""}`}
        </Typography>
      </Box>
    </Box>
  );
};

export default RunTestsNameRenderer;

RunTestsNameRenderer.propTypes = {
  data: PropTypes.object,
};
