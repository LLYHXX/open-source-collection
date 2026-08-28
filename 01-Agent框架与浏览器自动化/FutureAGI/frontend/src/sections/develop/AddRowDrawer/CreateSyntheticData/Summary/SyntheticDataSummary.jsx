import { Box, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";
import PropTypes from "prop-types";
import React from "react";

const SyntheticDataSummary = ({ showTitle = false }) => {
  return (
    <Box
      sx={(theme) => ({
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        backgroundColor: alpha(theme.palette.warning.main, 0.05),
        border: "1px solid",
        borderColor: alpha(theme.palette.warning.main, 0.2),
        padding: "12px",
        borderRadius: "4px",
      })}
    >
      {showTitle && (
        <Typography
          variant="s1"
          fontWeight={"fontWeightSemiBold"}
          color="text.primary"
        >
          Why Knowledge Base is important?
        </Typography>
      )}
      <Box>
        {syntheticDataSummary.map((item, index) => (
          <Box key={index} sx={{ display: "flex" }}>
            <Typography
              variant="s2"
              fontWeight={"fontWeightRegular"}
              color="text.primary"
            >
              {index + 1}.&nbsp;
            </Typography>
            <Typography
              variant="s2"
              fontWeight={"fontWeightRegular"}
              color="text.primary"
            >
              {item}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
};

export default SyntheticDataSummary;

SyntheticDataSummary.propTypes = {
  showTitle: PropTypes.bool,
};

const syntheticDataSummary = [
  "A knowledge base is vital for creating synthetic data because it ensures data consistency, realism, and relevance by defining relationships and rules.",
  "It allows for customized, accurate data generation based on specific needs, minimizes bias, and supports efficient, automated processes. ",
  "Additionally, it ensures compliance with data privacy regulations while providing realistic data for testing and model training.",
];
