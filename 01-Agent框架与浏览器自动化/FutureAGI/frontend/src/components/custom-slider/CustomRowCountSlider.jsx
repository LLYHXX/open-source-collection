import React from "react";
import PropTypes from "prop-types";
import { Slider } from "@mui/material";

const CustomRowCountSlider = ({
  value,
  onChange,
  onChangeCommitted,
  min = 0,
  max = 1000000000,
}) => {
  return (
    <Slider
      value={value}
      onChange={onChange}
      onChangeCommitted={onChangeCommitted}
      min={min}
      max={max}
      valueLabelDisplay="on"
      valueLabelFormat={(value) => {
        if (value >= 1000000000) return Math.floor(value / 1000000000) + "B"; // Convert to Billion
        if (value >= 1000000) return Math.floor(value / 1000000) + "M"; // Convert to Million
        return value; // Default case
      }}
      size="medium"
      sx={{
        color: "primary.main",
        "& .MuiSlider-rail": {
          backgroundColor: "action.disabledBackground",
          height: 6,
        },
        "& .MuiSlider-track": {
          height: 6,
        },
        "& .MuiSlider-thumb": {
          width: 16,
          height: 16,
          borderRadius: "50%",
          backgroundColor: "background.paper",
          border: "2px solid primary.main",
          transition: "0.2s ease-in-out",
          "&::before": {
            content: '""',
            width: 10,
            height: 10,
            backgroundColor: "action.disabledBackground",
            borderRadius: "50%",
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            transition: "0.2s ease-in-out",
          },
          "&:hover, &:focus": {
            width: 20,
            height: 20,
            "&::before": {
              width: 10,
              height: 10,
            },
          },
        },
      }}
    />
  );
};

CustomRowCountSlider.propTypes = {
  value: PropTypes.array.isRequired,
  onChange: PropTypes.func.isRequired,
  onChangeCommitted: PropTypes.func.isRequired,
  min: PropTypes.number,
  max: PropTypes.number,
};

export default CustomRowCountSlider;
