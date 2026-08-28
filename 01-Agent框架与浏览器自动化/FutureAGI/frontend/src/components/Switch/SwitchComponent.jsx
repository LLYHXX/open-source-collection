import { FormControlLabel, Switch } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const SwitchComponent = ({
  label,
  labelPlacement,
  labelStyle = {},
  ...rest
}) => {
  return (
    <FormControlLabel
      label={label}
      sx={{
        margin: 0,
        "& .MuiFormControlLabel-label": {
          ...labelStyle,
        },
      }}
      labelPlacement={labelPlacement ? labelPlacement : "start"}
      control={<Switch {...rest} />}
    ></FormControlLabel>
  );
};

export default SwitchComponent;

SwitchComponent.propTypes = {
  label: PropTypes.string,
  labelStyle: PropTypes.object,
  labelPlacement: PropTypes.oneOf(["start", "end", "top", "bottom"]),
};
