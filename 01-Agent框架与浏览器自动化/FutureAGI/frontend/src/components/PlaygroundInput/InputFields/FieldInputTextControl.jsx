import PropTypes from "prop-types";
import React from "react";
import { Controller } from "react-hook-form";
import FieldInputText from "./FieldInputText";

const FieldInputTextControl = ({
  control,
  fieldName,
  defaultValue = "",
  ...rest
}) => {
  return (
    <Controller
      rules={{ required: rest.required }}
      render={({
        field: { onChange, value, onBlur: defaultBlur, ref },
        formState: { errors },
      }) => (
        <FieldInputText
          {...rest}
          value={value}
          onChange={(e) => {
            onChange(e);
            rest?.onChange?.(e);
          }}
          onBlur={() => {
            defaultBlur();
            rest?.onBlur?.();
          }}
          inputRef={ref}
          error={
            !!fieldName.split(".").reduce((obj, key) => obj?.[key], errors)
              ?.message || rest?.error
          }
        />
      )}
      control={control}
      name={fieldName}
      defaultValue={defaultValue}
    />
  );
};

export default FieldInputTextControl;

FieldInputTextControl.propTypes = {
  control: PropTypes.any,
  fieldName: PropTypes.string,
  defaultValue: PropTypes.string,
};
