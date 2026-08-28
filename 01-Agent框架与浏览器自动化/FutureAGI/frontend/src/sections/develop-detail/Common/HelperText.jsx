import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const HelperText = ({ text, sx = {} }) => {
  return (
    <Box sx={{ display: "flex" }}>
      <Typography
        variant="s1"
        color="text.primary"
        fontWeight={"fontWeightRegular"}
        sx={{
          ...sx,
        }}
      >
        {text}
      </Typography>
    </Box>
  );
};

HelperText.propTypes = {
  text: PropTypes.string,
  sx: PropTypes.object,
};

export default HelperText;
