import _ from "lodash";
import PropTypes from "prop-types";
import React from "react";
import HelperText from "../HelperText";
import { camelCaseToTitleCase } from "src/utils/utils";
import FormTextFieldV2 from "src/components/FormTextField/FormTextFieldV2";

const ListInput = ({ control, fieldConfig, config, configKey }) => {
  const getHelperText = () => {
    let initialHelperText =
      config?.configParamsDesc?.[configKey] ||
      config?.config_params_desc?.[configKey] ||
      "";

    if (initialHelperText.length) {
      initialHelperText += ". ";
    }

    initialHelperText += "Please enter a comma separated string.";

    return initialHelperText;
  };

  return (
    <FormTextFieldV2
      control={control}
      defaultValue={fieldConfig?.default || ""}
      fieldName={`config.config.${configKey}`}
      placeholder="Enter key"
      helperText={<HelperText text={getHelperText()} />}
      size="small"
      label={camelCaseToTitleCase(configKey)}
    />
  );
};

ListInput.propTypes = {
  control: PropTypes.object,
  fieldConfig: PropTypes.object,
  config: PropTypes.object,
  configKey: PropTypes.string,
};

export default ListInput;
