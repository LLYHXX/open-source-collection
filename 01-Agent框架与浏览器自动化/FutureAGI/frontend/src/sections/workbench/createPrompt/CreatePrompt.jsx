import { Box, useTheme } from "@mui/material";
import React from "react";
import { ShowComponent } from "src/components/show";
import { AudioPlaybackProvider } from "../../../components/custom-audio/context-provider/AudioPlaybackContext";
import PromptContainer from "./PromptContainer";
import WorkbenchProvider from "./WorkbenchProvider";
import VersionHistoryDrawer from "./VersionHistory/VersionHistoryDrawer";
import { usePromptWorkbenchContext } from "./WorkbenchContext";
import CompareContainer from "./Compare/CompareContainer";
import LoadingTemplate from "../LoadingTemplate";
import { useLocation } from "react-router";

const WorkbenchContainers = () => {
  const { selectedVersions, loadingPrompt } = usePromptWorkbenchContext();
  const location = useLocation();

  const isSingleVersion = selectedVersions?.length <= 1;

  if (loadingPrompt && location?.state?.fromOption === "use-template") {
    return <LoadingTemplate />;
  }
  return (
    <>
      <AudioPlaybackProvider>
        <ShowComponent condition={isSingleVersion}>
          <PromptContainer />
        </ShowComponent>
        <ShowComponent condition={selectedVersions?.length > 1}>
          <CompareContainer />
        </ShowComponent>
      </AudioPlaybackProvider>
    </>
  );
};

const CreatePrompt = () => {
  const theme = useTheme();

  return (
    <WorkbenchProvider>
      <Box
        height={"100%"}
        sx={{
          backgroundColor: "background.paper",
          display: "flex",
          flexDirection: "column",
          gap: theme.spacing(3),
        }}
      >
        <Box
          height={"100%"}
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: theme.spacing(2),
            flexDirection: "column",
          }}
        >
          <WorkbenchContainers />
          <Box sx={{ padding: 2 }}>
            <VersionHistoryDrawer />
          </Box>
        </Box>
      </Box>
    </WorkbenchProvider>
  );
};

export default CreatePrompt;
