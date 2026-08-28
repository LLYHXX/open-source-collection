import _ from "lodash";
import PropTypes from "prop-types";
import React from "react";
import HelperText from "../HelperText";
import { camelCaseToTitleCase } from "src/utils/utils";
import FormTextFieldV2 from "src/components/FormTextField/FormTextFieldV2";

const StringInput = ({ control, fieldConfig, config, configKey }) => {
  const helperText =
    config?.configParamsDesc?.[configKey] ||
    config?.config_params_desc?.[configKey];

  return (
    <FormTextFieldV2
      control={control}
      defaultValue={fieldConfig?.default || ""}
      fieldName={`config.config.${configKey}`}
      placeholder="Enter key"
      helperText={<HelperText text={helperText} />}
      size="small"
      label={camelCaseToTitleCase(configKey)}
    />
  );
};

StringInput.propTypes = {
  control: PropTypes.object,
  fieldConfig: PropTypes.object,
  config: PropTypes.object,
  configKey: PropTypes.string,
};

export default StringInput;
