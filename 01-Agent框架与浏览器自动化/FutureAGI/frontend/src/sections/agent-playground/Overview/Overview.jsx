import React, { useEffect, useState } from "react";
import Versions from "./Versions";
import { Box, Divider, Stack } from "@mui/material";
import OverviewGraphPreview from "./OverviewGraphPreview";
import { useAgentPlaygroundStoreShallow } from "../store";

export default function Overview() {
  const { currentAgent } = useAgentPlaygroundStoreShallow((s) => {
    return {
      currentAgent: s.currentAgent,
    };
  });
  // Local selection state — initialized from store, changes as user clicks in sidebar
  const [selectedVersion, setSelectedVersion] = useState({
    version_id: currentAgent?.version_id ?? null,
    version_name: currentAgent?.version_name ?? "",
  });

  // Sync from store when currentAgent arrives (handles direct navigation)
  useEffect(() => {
    if (currentAgent?.version_id && !selectedVersion.version_id) {
      setSelectedVersion({
        version_id: currentAgent.version_id,
        version_name: currentAgent.version_name ?? "",
      });
    }
  }, [
    currentAgent?.version_id,
    currentAgent?.version_name,
    selectedVersion.version_id,
  ]);

  return (
    <Stack direction={"row"} height={"100%"}>
      <Box
        sx={{
          width: "230px",
          flexShrink: 0,
          overflow: "auto",
        }}
      >
        <Versions
          selectedVersion={selectedVersion.version_id}
          onVersionChange={(versionId, versionName) => {
            setSelectedVersion({
              version_id: versionId,
              version_name: versionName,
            });
          }}
        />
      </Box>
      <Divider orientation="vertical" />
      <OverviewGraphPreview
        selectedVersion={selectedVersion}
        currentVersion={currentAgent?.version_id}
      />
    </Stack>
  );
}
