import React, { useMemo } from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";
import { useFieldArray, useForm } from "react-hook-form";
import { FormSelectField } from "src/components/FormSelectField";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { useSearchParams } from "src/routes/hooks";
import { getMappedData } from "src/utils/connectors/big-query-utils";

import WizardInputHelpText from "../shared/WizardInputHelpText";
import BottomButtons from "../shared/BottomButtons";
import MappedTable from "../shared/MappedTable";
import SectionCard from "../shared/SectionCard";

import { MappingValidationSchema } from "./validation";

const getDefaultValues = (modelType, draftInfo) => {
  const isImageLLM = modelType === "GenerativeImage";
  if (draftInfo?.connMappings && Object.keys(draftInfo?.connMappings).length) {
    return draftInfo?.connMappings;
  }
  if (isImageLLM) {
    return {
      conversationId: "",
      timestamp: "",
      prompt: [
        { type: "text", columnName: "" },
        { type: "image", columnName: "" },
      ],
      response: [{ type: "text", columnName: "" }],
      modelType,
    };
  } else {
    return {
      conversationId: "",
      timestamp: "",
      prompt: [{ type: "text", columnName: "" }],
      response: [{ type: "text", columnName: "" }],
      modelType,
    };
  }
};

const Mapping = ({ setActiveStep, draftInfo }) => {
  const columns = draftInfo?.columns;

  const modelType = draftInfo?.aiModel?.modelType;

  const isImageLLM = modelType === "GenerativeImage";

  const queryClient = useQueryClient();

  const [searchParams] = useSearchParams();

  const draftId = searchParams.draftId;

  const userColumnOptions = columns?.length
    ? columns.map((v) => ({
        label: v,
        value: v,
      }))
    : [];

  const { control, handleSubmit, watch } = useForm({
    defaultValues: getDefaultValues(modelType, draftInfo),
    resolver: zodResolver(MappingValidationSchema),
  });

  const { fields: inputFields, append: addInputField } = useFieldArray({
    control: control,
    name: "prompt",
  });
  const { fields: outputFields, append: addOutputField } = useFieldArray({
    control: control,
    name: "response",
  });

  const allFormState = watch();

  const mappedData = useMemo(() => {
    return getMappedData(allFormState);
  }, [allFormState]);

  const { isPending: isSubmitting, mutate } = useMutation({
    mutationFn: (d) =>
      axios.put(`${endpoints.connectors.updateDraft}${draftId}/`, d),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["draft", draftId],
        type: "all",
      });
      setActiveStep(3);
    },
  });

  const onFormSubmit = (formValues) =>
    mutate({
      connMappings: {
        ...formValues,
        prompt: formValues.prompt.filter((p) => p.columnName.length),
      },
    });

  return (
    <>
      <Box
        sx={{
          display: "flex",
          gap: "43px",
          height: "100%",
          padding: "51px 52px 73px 52px",
          maxHeight: "100%",
          overflowY: "auto",
        }}
      >
        <Box
          sx={{
            flex: 1,
            overflow: "auto",
          }}
        >
          <Box sx={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <SectionCard title="Conversation ID and Timestamp">
              <Box
                sx={{
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 3.75,
                }}
              >
                <FormSelectField
                  control={control}
                  fieldName="conversationId"
                  options={userColumnOptions}
                  label="Conversation ID"
                  helperText={
                    <WizardInputHelpText text="The unique identifier of a specific prediction" />
                  }
                  MenuProps={{
                    PaperProps: {
                      sx: {
                        maxHeight: 150,
                      },
                    },
                  }}
                  valueSelector={(o) => o.value}
                />
                <FormSelectField
                  control={control}
                  fieldName="timestamp"
                  options={userColumnOptions}
                  label="Timestamp"
                  helperText={
                    <WizardInputHelpText text="The unique identifier of a specific prediction" />
                  }
                  MenuProps={{
                    PaperProps: {
                      sx: {
                        maxHeight: 150,
                      },
                    },
                  }}
                  valueSelector={(o) => o.value}
                />
              </Box>
            </SectionCard>
            <SectionCard
              title="Model Input"
              onActionButtonClick={
                isImageLLM
                  ? () => addInputField({ type: "image", columnName: "" })
                  : null
              }
              actionButtonText="Add image field"
            >
              <Box
                sx={{
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 3.75,
                }}
              >
                {inputFields.map((field, index) => {
                  return (
                    <FormSelectField
                      key={field.id}
                      control={control}
                      fieldName={`prompt.${index}.columnName`}
                      options={userColumnOptions}
                      label={`Model input ${field.type} field`}
                      MenuProps={{
                        PaperProps: {
                          sx: {
                            maxHeight: 150,
                          },
                        },
                      }}
                      helperText={
                        isImageLLM && index === 0 ? (
                          <WizardInputHelpText text="Optional" />
                        ) : (
                          ""
                        )
                      }
                      valueSelector={(o) => o.value}
                    />
                  );
                })}
              </Box>
            </SectionCard>
            <SectionCard
              title="Model Output"
              onActionButtonClick={
                isImageLLM
                  ? () => addOutputField({ type: "image", columnName: "" })
                  : null
              }
              actionButtonText="Add image field"
            >
              <Box
                sx={{
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 3.75,
                }}
              >
                {outputFields.map((field, index) => {
                  return (
                    <FormSelectField
                      key={field.id}
                      control={control}
                      fieldName={`response.${index}.columnName`}
                      options={userColumnOptions}
                      label={`Model output ${field.type} field`}
                      MenuProps={{
                        PaperProps: {
                          sx: {
                            maxHeight: 150,
                          },
                        },
                      }}
                      valueSelector={(o) => o.value}
                    />
                  );
                })}
              </Box>
            </SectionCard>
          </Box>
        </Box>
        <Box
          sx={{
            flex: 1,
            overflow: "auto",
            display: "flex",
            flexDirection: "column",
            height: "100%",
            gap: 1,
          }}
        >
          <MappedTable mappedData={mappedData} />
        </Box>
      </Box>
      <BottomButtons
        onNextClick={handleSubmit(onFormSubmit)}
        onBackClick={() => setActiveStep(1)}
        nextLoading={isSubmitting}
      />
    </>
  );
};

Mapping.propTypes = {
  setActiveStep: PropTypes.func,
  columns: PropTypes.object,
  modelType: PropTypes.string,
  draftInfo: PropTypes.object,
};

export default Mapping;
