import React from "react";
import FieldInputImage from "./FieldInputImage";
import { Controller } from "react-hook-form";
import PropTypes from "prop-types";

const FieldInputImageControl = ({ control, fieldName, ...rest }) => {
  return (
    <Controller
      rules={{ required: rest.required }}
      render={({ field: { onChange, value }, formState: { errors } }) => (
        <FieldInputImage
          {...rest}
          data={control ? value : value?.url}
          onChange={(e) => {
            onChange(e.url);
            rest?.onChange?.(e);
          }}
          error={
            !!fieldName.split(".").reduce((obj, key) => obj?.[key], errors)
              ?.message || rest?.error
          }
        />
      )}
      control={control}
      name={fieldName}
    />
  );
};

export default FieldInputImageControl;

FieldInputImageControl.propTypes = {
  control: PropTypes.any,
  fieldName: PropTypes.string,
};
