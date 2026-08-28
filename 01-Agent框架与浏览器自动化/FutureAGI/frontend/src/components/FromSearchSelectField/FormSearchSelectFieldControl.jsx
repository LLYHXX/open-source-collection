import React from "react";
import FormSearchSelectFieldState from "./FormSearchSelectFieldState";
import { Controller } from "react-hook-form";
import PropTypes from "prop-types";
import _ from "lodash";

const FormSearchSelectFieldControl = ({
  fieldName,
  control,
  defaultValue = "",
  showClear = true,
  onChange = (_e) => {},
  ...rest
}) => {
  return (
    <Controller
      render={({
        field: { onChange: handleOnChange, value, onBlur: defaultBlur, ref },
        formState: { errors },
      }) => {
        const errorMessage = _.get(errors, `${fieldName}.message`);
        const isError = !!errorMessage;

        return (
          <FormSearchSelectFieldState
            onChange={(e) => {
              onChange?.(e);
              handleOnChange(e);
            }}
            ref={ref}
            value={value}
            error={isError}
            showClear={showClear}
            helperText={errorMessage}
            onBlur={() => {
              defaultBlur();
              rest?.onBlur?.();
            }}
            {...rest}
          />
        );
      }}
      control={control}
      name={fieldName}
      defaultValue={defaultValue}
    />
  );
};

export default FormSearchSelectFieldControl;

FormSearchSelectFieldControl.propTypes = {
  fieldName: PropTypes.string,
  control: PropTypes.any,
  defaultValue: PropTypes.string,
  label: PropTypes.string,
  showClear: PropTypes.bool,
  onChange: PropTypes.func,
  skipUpdatingDirectly: PropTypes.bool,
};
