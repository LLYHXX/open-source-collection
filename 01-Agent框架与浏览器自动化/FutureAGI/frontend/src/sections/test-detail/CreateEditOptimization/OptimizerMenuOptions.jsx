import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import MenuItems from "src/components/FormSelectField/CustomMenuOptions";
import { Typography } from "@mui/material";

const OptimizerMenuOptions = ({ option: _option }) => {
  return (
    <MenuItems>
      <Box sx={{ display: "flex" }}>
        <Typography typography="m3"></Typography>
      </Box>
    </MenuItems>
  );
};

OptimizerMenuOptions.propTypes = {
  option: PropTypes.object,
};

export default OptimizerMenuOptions;
