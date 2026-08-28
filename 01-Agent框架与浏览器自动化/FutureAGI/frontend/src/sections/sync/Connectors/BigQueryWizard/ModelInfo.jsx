import { Alert, Box } from "@mui/material";
import React from "react";
import { useForm } from "react-hook-form";
import PropTypes from "prop-types";
import { FormSelectField } from "src/components/FormSelectField";
import {
  BigQueryMappedDummyData,
  EnvironmentOptions,
  ModelTypeOptions,
} from "src/utils/constant";
import { zodResolver } from "@hookform/resolvers/zod";
import { useSearchParams } from "src/routes/hooks";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import _ from "lodash";
import FormTextFieldV2 from "src/components/FormTextField/FormTextFieldV2";

import WizardInputHelpText from "../shared/WizardInputHelpText";
import MappedTable from "../shared/MappedTable";
import BottomButtons from "../shared/BottomButtons";
import SectionCard from "../shared/SectionCard";

import { ModelInfoValidationSchema } from "./validation";

const getDefaultData = (draftInfo) => {
  if (draftInfo?.aiModel && Object.keys(draftInfo?.aiModel).length) {
    const modelType = _.startCase(draftInfo?.aiModel?.modelType);
    const modelTypeId = ModelTypeOptions.find((o) => o.label === modelType);
    return {
      modelName: draftInfo?.aiModel?.userModelId,
      modelType: modelTypeId?.value,
      environment: draftInfo?.aiModel?.baselineModelEnvironment,
      version: draftInfo?.aiModel?.baselineModelVersion,
    };
  }

  return {
    modelName: "",
    modelType: "",
    environment: "",
    version: "",
  };
};

const ModelInfo = ({ setActiveStep, draftInfo }) => {
  const { control, handleSubmit } = useForm({
    defaultValues: getDefaultData(draftInfo),
    resolver: zodResolver(ModelInfoValidationSchema),
  });

  const queryClient = useQueryClient();

  const [searchParams] = useSearchParams();

  const draftId = searchParams.draftId;

  const {
    isPending: isSubmitting,
    mutate,
    isError,
    error,
  } = useMutation({
    mutationFn: (d) =>
      axios.put(
        `${endpoints.connectors.updateDraft}${searchParams.draftId}/`,
        d,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["draft", draftId],
        type: "all",
      });
      setActiveStep(2);
    },
  });

  const onNextClick = (formValues) => mutate({ ...formValues });

  const renderAlert = () => {
    if (!isError) {
      return <></>;
    }
    return (
      <Alert variant="standard" severity="error">
        {error?.message || "Something went wrong"}
      </Alert>
    );
  };

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
            <SectionCard title="Model Configuration">
              <Box
                sx={{
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 3.75,
                }}
              >
                <FormTextFieldV2
                  label="Model Name"
                  fullWidth
                  placeholder="Enter model name"
                  control={control}
                  fieldName="modelName"
                  helperText={
                    <WizardInputHelpText text="The name that the model will be given" />
                  }
                />
                <FormSelectField
                  control={control}
                  fieldName="modelType"
                  options={ModelTypeOptions}
                  label="Model Type"
                  helperText={
                    <WizardInputHelpText text="Determines which metric you can calculate" />
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
                  fieldName="environment"
                  options={EnvironmentOptions}
                  label="Environment"
                  helperText={
                    <WizardInputHelpText text="Environment of the model" />
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

                <FormTextFieldV2
                  label="Version"
                  fullWidth
                  control={control}
                  placeholder="Enter version"
                  fieldName="version"
                  helperText={
                    <WizardInputHelpText text="Version of the model" />
                  }
                />
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
          <MappedTable mappedData={BigQueryMappedDummyData} />
          {renderAlert()}
        </Box>
      </Box>
      <BottomButtons
        onNextClick={handleSubmit(onNextClick)}
        nextLoading={isSubmitting}
      />
    </>
  );
};

ModelInfo.propTypes = {
  setActiveStep: PropTypes.func,
  draftInfo: PropTypes.object,
};

export default ModelInfo;
