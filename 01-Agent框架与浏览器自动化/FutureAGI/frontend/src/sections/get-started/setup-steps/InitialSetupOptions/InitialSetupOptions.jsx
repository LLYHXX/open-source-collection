import { Box } from "@mui/material";
import React, { useMemo } from "react";
import BottomAction from "./BottomAction";
import PropTypes from "prop-types";
import CreateFirstDataset from "./CreateFirstDataset";
import CreateFirstEvaluation from "./CreateFirstEvaluation";
import KeySection from "./KeySection";
import CompleteSetup from "./CompleteSetup";
import RunFirstExperiment from "./RunFirstExperiment";
import SetupObsabilityInApplication from "./SetupObsabilityInApplication";
import InviteTeamMembers from "./InviteTeamMembers";
import { ShowComponent } from "src/components/show";

const componentFilter = {
  addKeys: {
    bottomAction: true,
    componentKey: "key",
  },
  createFirstDataset: {
    bottomAction: false,
    componentKey: "dataset",
  },
  createFirstEvaluation: {
    bottomAction: false,
    componentKey: "evals",
  },
  RunFirstExperiment: {
    bottomAction: true,
    componentKey: "experiment",
  },
  SetupObsabilityInApplication: {
    bottomAction: true,
    componentKey: "observe",
  },
  inviteTeamMembers: {
    bottomAction: true,
    componentKey: "invite",
  },
  complete: { bottomAction: false, componentKey: "complete" },
};

const InitialSetupOptions = ({ currentLabel, setCurrentLabel }) => {
  const { bottomAction, componentKey } = useMemo(() => {
    if (Object.prototype.hasOwnProperty.call(componentFilter, currentLabel)) {
      return componentFilter[currentLabel];
    }
    return { bottomAction: false, componentKey: "complete" };
  }, [currentLabel]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        backgroundColor: `background.paper`,
        width: "calc(100% - 290px)",
        overflow: "hidden",
      }}
    >
      <Box sx={{ flex: 1, padding: "16px 16px 0px", width: "100%" }}>
        <ShowComponent condition={componentKey === "key"}>
          <KeySection setCurrentLabel={setCurrentLabel} />
        </ShowComponent>
        <ShowComponent condition={componentKey === "dataset"}>
          <CreateFirstDataset setCurrentLabel={setCurrentLabel} />
        </ShowComponent>
        <ShowComponent condition={componentKey === "evals"}>
          <CreateFirstEvaluation setCurrentLabel={setCurrentLabel} />
        </ShowComponent>
        <ShowComponent condition={componentKey === "experiment"}>
          <RunFirstExperiment setCurrentLabel={setCurrentLabel} />
        </ShowComponent>
        <ShowComponent condition={componentKey === "observe"}>
          <SetupObsabilityInApplication setCurrentLabel={setCurrentLabel} />
        </ShowComponent>
        <ShowComponent condition={componentKey === "invite"}>
          <InviteTeamMembers />
        </ShowComponent>
        <ShowComponent condition={componentKey === "complete"}>
          <CompleteSetup />
        </ShowComponent>
      </Box>
      <ShowComponent condition={bottomAction}>
        <BottomAction
          currentLabel={currentLabel}
          setCurrentLabel={setCurrentLabel}
        />
      </ShowComponent>
    </Box>
  );
};

InitialSetupOptions.propTypes = {
  currentLabel: PropTypes.string,
  setCurrentLabel: PropTypes.func,
};

export default InitialSetupOptions;
