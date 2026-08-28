import { Box, Typography } from "@mui/material";
import React, { useState } from "react";
import PropTypes from "prop-types";
import { useController } from "react-hook-form";
import { TaskOptionsSlider } from "./TaskOptionSlider";
import Image from "src/components/image";
import CustomTooltip from "src/components/tooltip";

// Input section with label and tooltip
const InputSection = ({ children, label }) => {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <Typography variant="s1" color="text.primary">
          {label}
        </Typography>
        <CustomTooltip
          show={true}
          title="Sampling rate (%) defines the percentage of data sampled for the task, ranging from 0 to 100. For example, 50% means half of the data is used"
          placement="top"
          arrow
          type="black"
        >
          <Image
            src="/icons/datasets/i-icon.svg"
            style={{ marginBottom: "3px" }}
          />
        </CustomTooltip>
      </Box>
      {children}
    </Box>
  );
};

// NewTaskSlider component
const NewTaskSlider = ({ label, control, fieldName, ...rest }) => {
  const {
    field: { value, onChange, onBlur, ref },
    fieldState: { error },
  } = useController({ control, name: fieldName });

  const [sliderValue, setSliderValue] = useState(value ?? 1);

  const marks = [
    { value: 1, label: 1 },
    { value: 20, label: 20 },
    { value: 40, label: 40 },
    { value: 60, label: 60 },
    { value: 80, label: 80 },
    { value: 100, label: 100 },
  ];

  return (
    <Box>
      <Box sx={{ paddingLeft: 1.5, paddingRight: 3 }}>
        <InputSection label={label}></InputSection>
      </Box>
      <Box sx={{ paddingX: 1 }}>
        <TaskOptionsSlider
          {...rest}
          value={sliderValue}
          onChange={(e, newValue) => {
            setSliderValue(newValue);
            onChange(newValue);
          }}
          onBlur={onBlur}
          inputRef={ref}
          aria-label={label}
          valueLabelDisplay="auto"
          size="medium"
          marks={marks}
        />
      </Box>
      {error && (
        <Typography variant="caption" color="error">
          {error.message}
        </Typography>
      )}
    </Box>
  );
};

NewTaskSlider.propTypes = {
  label: PropTypes.string.isRequired,
  control: PropTypes.object.isRequired,
  fieldName: PropTypes.string.isRequired,
  min: PropTypes.number,
  max: PropTypes.number,
  step: PropTypes.number,
};

InputSection.propTypes = {
  children: PropTypes.node,
  label: PropTypes.string.isRequired,
};

export default NewTaskSlider;
