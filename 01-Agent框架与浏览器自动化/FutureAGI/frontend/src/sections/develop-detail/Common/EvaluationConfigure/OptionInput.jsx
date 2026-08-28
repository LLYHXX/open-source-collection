import PropTypes from "prop-types";
import React from "react";
import { FormSelectField } from "src/components/FormSelectField";
import HelperText from "../HelperText";
import { camelCaseToTitleCase } from "src/utils/utils";
const OptionInput = ({ control, config, configKey }) => {
  const options =
    config?.configParamsOption?.[configKey] ||
    config?.config_params_option?.[configKey] ||
    [];
  const helperText =
    config?.configParamsDesc?.[configKey] ||
    config?.config_params_desc?.[configKey];

  const selectOptions = options.map((option) => ({
    label: option,
    value: option,
  }));

  return (
    <FormSelectField
      control={control}
      defaultValue={config?.config?.[configKey] || ""}
      fieldName={`config.config.${configKey}`}
      options={selectOptions}
      helperText={<HelperText text={helperText} />}
      fullWidth
      size="small"
      label={camelCaseToTitleCase(configKey)}
      MenuProps={{
        PaperProps: {
          sx: {
            maxHeight: 200,
          },
        },
      }}
    />
  );
};

OptionInput.propTypes = {
  control: PropTypes.object,
  fieldConfig: PropTypes.object,
  config: PropTypes.object,
  configKey: PropTypes.string,
};

export default OptionInput;
