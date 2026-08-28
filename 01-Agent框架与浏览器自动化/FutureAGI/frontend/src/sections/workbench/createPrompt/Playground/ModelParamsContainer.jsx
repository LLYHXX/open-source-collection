import PropTypes from "prop-types";
import React, { useEffect } from "react";
import { useForm } from "react-hook-form";
import CustomModelOptions from "src/components/custom-model-options/CustomModelOptions";
import { Events, PropertyName, trackEvent } from "src/utils/Mixpanel";
import { PERMISSIONS, RolePermission } from "src/utils/rolePermissionMapping";

export default function ModelParamsContainer({
  initialModelParams,
  responseSchema,
  modelOptionChange,
  selectedVersions,
  promptIndex,
  modelConfig,
  id,
  userRole,
  transformedModelParams,
  voiceOptions,
  disabled = false,
}) {
  const {
    control,
    getValues,
    setValue,
    reset,
    formState: { isDirty },
  } = useForm();

  useEffect(() => {
    reset({
      config: initialModelParams,
    });
  }, [initialModelParams, reset]);

  const handleApply = () => {
    const config = getValues("config");
    const response = responseSchema.find(
      (item) => item.id === config.responseFormat,
    );

    modelOptionChange({
      ...config,
      ...(response && { responseFormat: response }),
    });
  };
  return (
    <CustomModelOptions
      isModalContainer={true}
      control={control}
      handleApply={handleApply}
      reset={reset}
      responseSchema={responseSchema}
      disabledClick={
        disabled || !RolePermission.PROMPTS[PERMISSIONS.DELETE][userRole]
      }
      setValue={setValue}
      modelConfig={modelConfig}
      isDirty={isDirty}
      disabledHover
      onClick={() => {
        trackEvent(Events.promptParamsClicked, {
          [PropertyName.promptId]: id,
          [PropertyName.version]: selectedVersions?.[promptIndex]?.version,
        });
      }}
      modelParams={transformedModelParams}
      voiceOptions={voiceOptions}
    />
  );
}

ModelParamsContainer.propTypes = {
  initialModelParams: PropTypes.object.isRequired,
  responseSchema: PropTypes.array.isRequired,
  modelOptionChange: PropTypes.func.isRequired,
  selectedVersions: PropTypes.array.isRequired,
  promptIndex: PropTypes.number.isRequired,
  modelConfig: PropTypes.object.isRequired,
  id: PropTypes.string.isRequired,
  userRole: PropTypes.string.isRequired,
  transformedModelParams: PropTypes.object.isRequired,
  voiceOptions: PropTypes.object,
  disabled: PropTypes.bool,
};
