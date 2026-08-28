import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { PromptSection } from "src/components/prompt-section";
import { camelCaseToTitleCase } from "src/utils/utils";
import HelperText from "../HelperText";

const PromptInput = ({
  control,
  config,
  configKey,
  allColumns,
  jsonSchemas = {},
}) => {
  const helperText =
    config?.configParamsDesc?.[configKey] ||
    config?.config_params_desc?.[configKey];

  return (
    <Box sx={{ display: "flex", gap: 1, flexDirection: "column" }}>
      <Box sx={{ display: "flex", gap: 0.5, flexDirection: "column" }}>
        <Typography variant="body2">
          {camelCaseToTitleCase(configKey)}
        </Typography>
        <HelperText text={helperText} />
      </Box>
      <PromptSection
        allColumns={allColumns}
        jsonSchemas={jsonSchemas}
        control={control}
        contentSuffix=""
        onRemove={undefined}
        roleSelectDisabled={true}
        hideSelectRole={true}
        prefixControlString={`config.config.${configKey}`}
        roleSuffix=""
      />
    </Box>
  );
};

PromptInput.propTypes = {
  control: PropTypes.object,
  fieldConfig: PropTypes.object,
  config: PropTypes.object,
  configKey: PropTypes.string,
  allColumns: PropTypes.array,
  jsonSchemas: PropTypes.object,
};

export default PromptInput;
