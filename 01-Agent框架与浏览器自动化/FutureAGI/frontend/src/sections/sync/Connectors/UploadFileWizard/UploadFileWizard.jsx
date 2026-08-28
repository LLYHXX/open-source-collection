import { Box, LinearProgress, Step, Stepper } from "@mui/material";
import React, { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { useSearchParams } from "src/routes/hooks";
import { useNavigate } from "react-router";
import {
  WizardConnector,
  WizardStepIcon,
  WizardStepLabel,
} from "../shared/WizardStepper";
import ModelInfo from "../BigQueryWizard/ModelInfo";
import ExtraInfo from "../BigQueryWizard/ExtraInfo";
import StartJob from "./StartJob";
import UploadFile from "./UploadFile";
import Mapping from "./Mapping";

const steps = [
  "Upload CSV",
  "Model Info",
  "Mapping",
  "Extra Info",
  "Start Job",
];

const UploadFileWizard = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [searchParams, setSearchParam] = useSearchParams({});

  const draftId = searchParams.draftId;

  const { data: draftData, isFetching: draftIdLoading } = useQuery({
    queryKey: ["draftId"],
    queryFn: () => axios.get(endpoints.connectors.getDraftId),
    enabled: !draftId?.length,
    select: (d) => d.data,
  });

  const navigate = useNavigate();

  const onCloseClick = () => {
    setSearchParam({ draftId: null });
    navigate("/dashboard/sync/connectors");
  };

  useEffect(() => {
    if (!draftId?.length && draftData) {
      setSearchParam({ draftId: draftData.result.draftUuid });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draftData]);

  const { data: draftInfo, isFetching: draftLoading } = useQuery({
    queryKey: ["draft", draftId],
    queryFn: () => axios.get(`${endpoints.connectors.getDraftData}${draftId}/`),
    enabled: Boolean(draftId?.length),
    select: (d) => d.data?.result,
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    if (!draftInfo) {
      return;
    }
    if (draftInfo?.tags && draftInfo?.tags?.length) {
      setActiveStep(4);
    } else if (
      draftInfo?.connMappings &&
      Object.keys(draftInfo?.connMappings).length
    ) {
      setActiveStep(3);
    } else if (draftInfo?.aiModel) {
      setActiveStep(2);
    } else if (draftInfo?.columns && draftInfo?.columns?.length) {
      setActiveStep(1);
    } else {
      setActiveStep(0);
    }
  }, [draftInfo]);

  const renderWizardStep = () => {
    switch (activeStep) {
      case 0:
        return (
          <UploadFile setActiveStep={setActiveStep} onClose={onCloseClick} />
        );
      case 1:
        return (
          <ModelInfo setActiveStep={setActiveStep} draftInfo={draftInfo} />
        );
      case 2:
        return <Mapping setActiveStep={setActiveStep} draftInfo={draftInfo} />;
      case 3:
        return (
          <ExtraInfo setActiveStep={setActiveStep} draftInfo={draftInfo} />
        );
      case 4:
        return (
          <StartJob
            onClose={onCloseClick}
            connMappings={draftInfo?.connMappings}
            tags={draftInfo?.tags}
            modelInfo={draftInfo?.aiModel}
            sourceConfig={draftInfo?.sourceConfig}
            setActiveStep={setActiveStep}
          />
        );
      default:
        break;
    }
  };

  const showLinearProgress = draftIdLoading || draftLoading;

  if (showLinearProgress) {
    return <LinearProgress />;
  }

  return (
    <>
      <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
        <Box sx={{ width: "80%", marginTop: 4.5 }}>
          <Stepper
            alternativeLabel
            activeStep={activeStep}
            connector={<WizardConnector />}
          >
            {steps.map((label) => (
              <Step key={label}>
                <WizardStepLabel StepIconComponent={WizardStepIcon}>
                  {label}
                </WizardStepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>
        {showLinearProgress ? <></> : renderWizardStep()}
      </Box>
    </>
  );
};

export default UploadFileWizard;
