import PropTypes from "prop-types";
import React from "react";
import HelperText from "../HelperText";
import { camelCaseToTitleCase } from "src/utils/utils";
import FormTextFieldV2 from "src/components/FormTextField/FormTextFieldV2";

const NumberInput = ({ control, config, configKey }) => {
  const helperText =
    config?.configParamsDesc?.[configKey] ||
    config?.config_params_desc?.[configKey];

  return (
    <FormTextFieldV2
      fieldType="number"
      control={control}
      placeholder="Enter number"
      fieldName={`config.config.${configKey}`}
      defaultValue={config?.config?.[configKey] || ""}
      helperText={<HelperText text={helperText} />}
      size="small"
      label={camelCaseToTitleCase(configKey)}
      inputProps={{
        inputMode: "numeric",
        pattern: "[0-9]*",
        min: 1,
        // onInput: (e) => {
        //   e.target.value = e.target.value.replace(/[^0-9.]/g, "");
        // },
      }}
    />
  );
};

NumberInput.propTypes = {
  control: PropTypes.object,
  fieldConfig: PropTypes.object,
  config: PropTypes.object,
  configKey: PropTypes.string,
};

export default NumberInput;
