import { Box, Button, Typography } from "@mui/material";
import React from "react";
import Iconify from "src/components/iconify";
import PropTypes from "prop-types";

const NoAnnotationLabelsSection = ({ onCreateLabel }) => {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flex: 1,
        flexDirection: "column",
        gap: "12px",
      }}
    >
      <Typography variant="s1">No annotations yet</Typography>
      <Button
        variant="outlined"
        color="primary"
        size="small"
        startIcon={<Iconify icon="mingcute:add-line" width={16} height={16} />}
        onClick={onCreateLabel}
      >
        Add Label
      </Button>
    </Box>
  );
};

NoAnnotationLabelsSection.propTypes = {
  onCreateLabel: PropTypes.func,
};

export default NoAnnotationLabelsSection;
