import React from "react";
import PropTypes from "prop-types";
import { Controller } from "react-hook-form";

import Slider from "@mui/material/Slider";
import FormHelperText from "@mui/material/FormHelperText";
import { Typography } from "@mui/material";

// ----------------------------------------------------------------------

export default function RHFSlider({
  name,
  control,
  helperText,
  label = "",
  ...other
}) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => {
        return (
          <>
            <Typography typography="s2_1" fontWeight="fontWeightMedium">
              {label}
            </Typography>
            <Slider {...field} valueLabelDisplay="auto" {...other} />

            {(!!error || helperText) && (
              <FormHelperText error={!!error}>
                {error ? error?.message : helperText}
              </FormHelperText>
            )}
          </>
        );
      }}
    />
  );
}

RHFSlider.propTypes = {
  helperText: PropTypes.string,
  control: PropTypes.object,
  label: PropTypes.string,
  name: PropTypes.string,
};
