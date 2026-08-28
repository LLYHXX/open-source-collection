import { Box, Button } from "@mui/material";
import React from "react";
import IncrementerButton from "src/components/IncrementerButton/IncrementerButton";
import PropTypes from "prop-types";
import InputSection from "./InputSection";
import { ModelOptionSlider } from "./ModelOptionSlider";
import { ShowComponent } from "src/components/show";
import CustomTooltip from "src/components/tooltip";
import _ from "lodash";

function generateMarks({ min, max, step }) {
  const steps = (max - min) / step;
  return Array.from({ length: steps }, (_, i) => ({
    value: parseFloat((min + i * step).toFixed(6)), // prevent float errors
    label: "", // optional label
  }));
}

const SliderRowState = ({
  label,
  value,
  onChange,
  inputSectionStyles,
  sliderContainerStyles,
  labelProps = {},
  showClearButton = false,
  tooltipText,
  disabled = false,
  ...rest
}) => {
  const isNull = value == null;

  const handleIncrease = () => {
    if (isNull) {
      onChange(rest.min ?? 0);
      return;
    }
    onChange(Math.min(value + (rest.step || 1), rest.max ?? Infinity));
  };

  const handleDecrease = () => {
    if (isNull) return;
    onChange(Math.max(value - (rest.step || 1), rest.min ?? -Infinity));
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        ...(disabled && { opacity: 0.5, pointerEvents: "none" }),
      }}
    >
      <InputSection
        label={
          <CustomTooltip
            show={tooltipText ? true : false}
            title={tooltipText}
            placement="bottom"
            arrow
            size="small"
            type="black"
            slotProps={{
              tooltip: {
                sx: {
                  maxWidth: "200px !important",
                },
              },
            }}
          >
            <span>{_.startCase(label)}</span>
          </CustomTooltip>
        }
        sx={inputSectionStyles || {}}
        labelProps={labelProps}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <IncrementerButton
            quantity={isNull ? null : parseFloat(value?.toFixed(2))}
            onIncrease={handleIncrease}
            onDecrease={handleDecrease}
            disabledIncrease={
              disabled ||
              (rest.max !== undefined && !isNull && value >= rest.max)
            }
            disabledDecrease={
              disabled ||
              isNull ||
              (rest.min !== undefined && value <= rest.min)
            }
            sx={{ height: "25px", borderRadius: "4px", m: 0 }}
          />
          <ShowComponent condition={showClearButton}>
            <Button
              size="small"
              onClick={() => onChange(null)}
              sx={{ textDecoration: "underline" }}
            >
              Clear
            </Button>
          </ShowComponent>
        </Box>
      </InputSection>

      <Box sx={sliderContainerStyles}>
        <ModelOptionSlider
          {...rest}
          aria-label="Slider"
          valueLabelDisplay={isNull ? "off" : "auto"}
          valueLabelFormat={(val) => val?.toFixed(2)}
          size="medium"
          value={isNull ? rest?.min ?? 0 : value}
          // Initialize value before drag starts when null.
          // Without this, the value prop source changes mid-drag (fallback → field.value),
          // which disrupts MUI Slider's pointer tracking and closes the parent popover.
          onPointerDown={() => {
            if (isNull) {
              onChange(rest?.min ?? 0);
            }
          }}
          onChange={(_, val) => onChange(val)}
          disabled={disabled}
          {...(rest.showMark && {
            marks: generateMarks(rest),
            sx: { ...rest?.sx },
          })}
        />
      </Box>
    </Box>
  );
};

SliderRowState.propTypes = {
  label: PropTypes.string,
  value: PropTypes.number,
  onChange: PropTypes.func.isRequired,
  inputSectionStyles: PropTypes.any,
  sliderContainerStyles: PropTypes.any,
  labelProps: PropTypes.object,
  showClearButton: PropTypes.bool,
  tooltipText: PropTypes.string,
  disabled: PropTypes.bool,
};

export default SliderRowState;
