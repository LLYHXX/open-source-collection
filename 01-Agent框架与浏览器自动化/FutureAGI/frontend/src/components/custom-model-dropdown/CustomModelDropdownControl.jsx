import React from "react";
import PropTypes from "prop-types";
import { Controller, useController } from "react-hook-form";
import CustomModelDropdown from "./CustomModelDropdown";
import _ from "lodash";

const CustomModelDropdownControl = ({
  fieldName,
  control,
  fieldPrefix,
  modelObjectKey = "modelDetail",
  extraParams = {},
  ...rest
}) => {
  const { field } = useController({
    name: `${fieldPrefix ? `${fieldPrefix}.` : ""}${modelObjectKey}`,
    control,
  });

  return (
    <>
      <Controller
        render={({
          field: { onChange, value, ref },
          formState: { errors },
        }) => {
          const fieldError = {
            isError: false,
            errorMessage: "",
          };

          const path = fieldPrefix ? `${fieldPrefix}.${fieldName}` : fieldName;
          const errorObj = _.get(errors, path);

          fieldError.isError = Boolean(errorObj);
          fieldError.errorMessage = errorObj?.message ?? "";

          return (
            <CustomModelDropdown
              {...rest}
              onChange={(e) => {
                if (rest.multiple) {
                  // For multiple selection, pass the array directly
                  onChange(e);
                } else {
                  const value = {
                    target: {
                      ...e.target,
                      value: e?.target?.value?.model_name,
                    },
                  };
                  onChange(value);
                }
                if (modelObjectKey) {
                  field?.onChange?.(e);
                }
                rest?.onChange?.(e);
              }}
              modelRef={ref}
              value={value}
              modelDetail={field?.value ?? {}}
              error={fieldError?.isError}
              helperText={fieldError?.errorMessage}
              extraParams={extraParams}
            />
          );
        }}
        control={control}
        name={`${fieldPrefix ? `${fieldPrefix}.` : ""}${fieldName}`}
      />
    </>
  );
};

export default CustomModelDropdownControl;

CustomModelDropdownControl.propTypes = {
  fieldName: PropTypes.string,
  control: PropTypes.any,
  fieldPrefix: PropTypes.string,
  modelObjectKey: PropTypes.string,
  extraParams: PropTypes.object,
  customTrigger: PropTypes.oneOfType([PropTypes.node, PropTypes.func]),
};
