import PropTypes from "prop-types";
import React from "react";
import { Controller } from "react-hook-form";
import SwitchComponent from "./SwitchComponent";

const SwitchField = ({
  control,
  fieldName,
  label,
  labelPlacement,
  onChange,
  ...rest
}) => {
  return (
    <Controller
      render={({ field }) => (
        <SwitchComponent
          label={label}
          labelPlacement={labelPlacement}
          {...rest}
          checked={field.value}
          onChange={(e) => {
            field.onChange(e);
            onChange?.(e);
          }}
        />
      )}
      control={control}
      name={fieldName}
    ></Controller>
  );
};

export default SwitchField;

SwitchField.propTypes = {
  control: PropTypes.object,
  fieldName: PropTypes.string,
  label: PropTypes.string,
  labelPlacement: PropTypes.oneOf(["start", "end", "top", "bottom"]),
  onChange: PropTypes.func,
};
