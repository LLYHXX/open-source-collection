import { Box, LinearProgress, Step, Stepper } from "@mui/material";
import React, { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { useSearchParams } from "src/routes/hooks";
import { useNavigate } from "react-router";

import {
  WizardConnector,
  WizardStepIcon,
  WizardStepLabel,
} from "../shared/WizardStepper";
import Mapping from "../UploadFileWizard/Mapping";

import TablePermission from "./TablePermission";
import ModelInfo from "./ModelInfo";
import ExtraInfo from "./ExtraInfo";
import StartJob from "./StartJob";

const steps = [
  "Table Permission",
  "Model Info",
  "Mapping",
  "Extra Info",
  "Start Job",
];

const BigQueryWizard = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [searchParams, setSearchParam] = useSearchParams({});

  const queryClient = useQueryClient();

  const navigate = useNavigate();

  const draftId = searchParams.draftId;

  const { data: draftData, isFetching: draftIdLoading } = useQuery({
    queryKey: ["draftId"],
    queryFn: () => axios.get(endpoints.connectors.getDraftId),
    enabled: !draftId?.length,
    select: (d) => d.data,
  });

  const onCloseClick = () => {
    setSearchParam({ draftId: null });
    navigate("/dashboard/sync/connectors");
    queryClient.removeQueries({ queryKey: ["draftId"], type: "all" });
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
      // ai model is there means show mapping
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
          <TablePermission
            setActiveStep={setActiveStep}
            onClose={onCloseClick}
          />
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

BigQueryWizard.propTypes = {};

export default BigQueryWizard;
