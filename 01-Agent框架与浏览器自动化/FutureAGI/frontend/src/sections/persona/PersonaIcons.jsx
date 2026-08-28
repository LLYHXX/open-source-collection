import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import SvgColor from "src/components/svg-color";

const PersonaIcons = ({ imgSrc, imgStyles }) => {
  return (
    <Box
      sx={{
        width: "30px",
        height: "30px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <SvgColor src={imgSrc} sx={imgStyles} />
    </Box>
  );
};

PersonaIcons.propTypes = {
  imgSrc: PropTypes.string,
  imgStyles: PropTypes.object,
};

export default PersonaIcons;
