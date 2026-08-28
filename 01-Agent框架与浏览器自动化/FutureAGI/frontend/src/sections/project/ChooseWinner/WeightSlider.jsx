import PropTypes from "prop-types";
import React from "react";
import SliderRow from "src/sections/common/SliderRow/SliderRow";
import { useTheme } from "@mui/material";

import { weightSliderMarks } from "./common";

const WeightSlider = ({ control, fieldName, label }) => {
  const theme = useTheme();
  return (
    <SliderRow
      control={control}
      fieldName={fieldName}
      label={label}
      marks={weightSliderMarks}
      min={0}
      max={10}
      sliderContainerStyles={{
        px: theme.spacing(0.75),
      }}
      sx={{
        "& .MuiSlider-markLabel": {
          whiteSpace: "normal",
          textAlign: "center",
          maxWidth: "60px",
          transform: "unset",
          top: theme.spacing(2),
          color: "text.disabled",
          fontWeight: "fontWeightRegular",
          ...theme.typography.s2,
        },
        "& .MuiSlider-markLabel[data-index='5']": {
          right: "-5px",
          left: "unset !important",
        },
        "& .MuiSlider-mark": {
          backgroundColor: "action.selected",
        },
        marginBottom: "0",
      }}
    />
  );
};

WeightSlider.propTypes = {
  control: PropTypes.object,
  fieldName: PropTypes.string,
  label: PropTypes.string,
};

export default WeightSlider;
