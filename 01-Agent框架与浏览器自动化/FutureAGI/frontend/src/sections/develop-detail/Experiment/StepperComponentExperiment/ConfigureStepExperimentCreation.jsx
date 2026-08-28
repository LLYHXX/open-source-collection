import { Stack } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import StepsHeaderComponent from "./StepsHeaderComponent";
import { useWatch } from "react-hook-form";
import { ShowComponent } from "src/components/show";

import ConfigureStepSTT from "./ConfigureStepSTT";
import ConfigureStepLLM from "./ConfigureStepLLM";
import ConfigureStepTTS from "./ConfigureStepTTS";
import { MODEL_TYPES } from "../../RunPrompt/common";
import { getOutputOptions } from "../common";
import { FormSearchSelectFieldControl } from "src/components/FromSearchSelectField";
import EditExperimentCopy from "./EditExperimentCopy";
const ConfigureStepExperimentCreation = ({
  control,
  allColumns,
  getValues,
  setValue,
  unregister,
  clearErrors,
  errors,
  watch,
  jsonSchemas,
  setError,
  isEditing = false,
  derivedVariables,
}) => {
  const watchModelType = useWatch({
    control,
    name: "experimentType",
  });
  const watchName = useWatch({
    control,
    name: "name",
  });
  return (
    <Stack spacing={2}>
      <StepsHeaderComponent
        title={"Configure prompts/agents "}
        subtitle={"Configure prompts to compare their outputs side by side"}
      />
      <ShowComponent condition={isEditing}>
        <EditExperimentCopy name={watchName} type={watchModelType} />
      </ShowComponent>

      <ShowComponent condition={watchModelType === MODEL_TYPES.LLM}>
        <ConfigureStepLLM
          unregister={unregister}
          watch={watch}
          getValues={getValues}
          control={control}
          setValue={setValue}
          errors={errors}
          setError={setError}
          clearErrors={clearErrors}
          jsonSchemas={jsonSchemas}
          allColumns={allColumns}
          isEditing={isEditing}
        />
      </ShowComponent>
      <ShowComponent
        condition={
          watchModelType === MODEL_TYPES.TTS ||
          watchModelType === MODEL_TYPES.IMAGE
        }
      >
        <ConfigureStepTTS
          control={control}
          allColumns={allColumns}
          setValue={setValue}
          clearErrors={clearErrors}
          errors={errors}
          watch={watch}
          jsonSchemas={jsonSchemas}
          getValues={getValues}
          derivedVariables={derivedVariables}
          unregister={unregister}
        />
      </ShowComponent>
      <ShowComponent condition={watchModelType === MODEL_TYPES.STT}>
        <ConfigureStepSTT
          unregister={unregister}
          allColumns={allColumns}
          control={control}
          fieldPrefix={`promptConfig.0`}
          getValues={getValues}
          setValue={setValue}
        />
      </ShowComponent>
      <ShowComponent condition={watchModelType !== MODEL_TYPES.LLM}>
        <FormSearchSelectFieldControl
          fullWidth
          label="Output Format"
          size="small"
          required={true}
          control={control}
          fieldName="outputFormat"
          disabled={
            watchModelType === MODEL_TYPES.TTS ||
            watchModelType === MODEL_TYPES.IMAGE
          }
          options={getOutputOptions[watchModelType] || []}
        />
      </ShowComponent>
    </Stack>
  );
};

export default ConfigureStepExperimentCreation;

ConfigureStepExperimentCreation.propTypes = {
  control: PropTypes.object,
  errors: PropTypes.object.isRequired,
  allColumns: PropTypes.array,
  getValues: PropTypes.func,
  setValue: PropTypes.func,
  unregister: PropTypes.func,
  clearErrors: PropTypes.func,
  watch: PropTypes.func,
  jsonSchemas: PropTypes.any,
  setError: PropTypes.func,
  isEditing: PropTypes.bool,
  derivedVariables: PropTypes.bool,
};
