import PropTypes from "prop-types";
import React from "react";
import { FormCheckboxField } from "src/components/FormCheckboxField";
import _ from "lodash";
import { Box } from "@mui/material";
import { camelCaseToTitleCase } from "src/utils/utils";
import HelperText from "../HelperText";

const BooleanInput = ({ control, config, configKey }) => {
  const helperText =
    config?.configParamsDesc?.[configKey] ||
    config?.config_params_desc?.[configKey];

  return (
    <Box>
      <FormCheckboxField
        control={control}
        defaultValue={!!config?.config?.[configKey]}
        fieldName={`config.config.${configKey}`}
        helperText={<HelperText text={helperText} />}
        size="small"
        label={camelCaseToTitleCase(configKey)}
        labelPlacement="start"
      />
    </Box>
  );
};

BooleanInput.propTypes = {
  control: PropTypes.object,
  fieldConfig: PropTypes.object,
  config: PropTypes.object,
  configKey: PropTypes.string,
};

export default BooleanInput;
