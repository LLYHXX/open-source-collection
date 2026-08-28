import PropTypes from "prop-types";
import React from "react";
import { Box, Typography, Divider } from "@mui/material";

const EditExperimentCopy = ({ name, type }) => {
  return (
    <Box
      sx={{
        backgroundColor: "blue.o5",
        border: "1px solid",
        borderColor: "blue.o10",
        borderRadius: 0.25,
        padding: 1.5,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      {/* Experiment Name - Text Only */}
      <Box flex={1} pr={3}>
        <Typography
          variant="s2_1"
          sx={{
            display: "block",
            mb: 1,
            color: "text.disabled",
          }}
          fontWeight={"fontWeightRegular"}
        >
          Experiment name
        </Typography>
        <Typography
          variant="m3"
          fontWeight={"fontWeightMedium"}
          sx={{
            color: "text.primary",
          }}
        >
          {name}
        </Typography>
      </Box>
      <Divider
        orientation="vertical"
        flexItem
        sx={{ mx: 2, borderColor: "blue.o10" }}
      />
      {/* Experiment Type - Text Only */}
      <Box flex={1}>
        <Typography
          variant="s2_1"
          sx={{
            display: "block",
            mb: 1,
            color: "text.disabled",
          }}
          fontWeight={"fontWeightRegular"}
        >
          Experiment type
        </Typography>
        <Typography
          variant="m3"
          fontWeight={"fontWeightMedium"}
          sx={{
            color: "text.primary",
          }}
        >
          {type?.toUpperCase()}
        </Typography>
      </Box>
    </Box>
  );
};

EditExperimentCopy.propTypes = {
  name: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
};

export default EditExperimentCopy;
