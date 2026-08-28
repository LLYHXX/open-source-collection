import React from "react";
import PropTypes from "prop-types";
import { Controller } from "react-hook-form";
import _ from "lodash";
import { FormControl, FormHelperText } from "@mui/material";
import { DatePicker } from "@mui/x-date-pickers";

export const FormDateField = ({ fieldName, control, fullWidth, ...rest }) => {
  return (
    <Controller
      render={({ field, formState: { errors } }) => {
        const errorMessage = _.get(errors, `${fieldName}.message`);
        const isError = !!errorMessage;
        return (
          <FormControl size={rest.size} error={isError} fullWidth={fullWidth}>
            <DatePicker {...rest} {...field} label={rest?.label} />
            {isError && <FormHelperText>{errorMessage}</FormHelperText>}
          </FormControl>
        );
      }}
      control={control}
      name={fieldName}
    />
  );
};

FormDateField.propTypes = {
  control: PropTypes.any,
  fieldName: PropTypes.string.isRequired,
  fullWidth: PropTypes.bool,
};
