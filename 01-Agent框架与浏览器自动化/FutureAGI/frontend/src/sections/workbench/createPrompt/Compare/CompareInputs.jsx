import { Box } from "@mui/material";
import React, { useCallback, useState } from "react";
import { PromptRoles } from "src/utils/constants";
import { getRandomId } from "src/utils/utils";

import { usePromptWorkbenchContext } from "../WorkbenchContext";
import SaveAndCommit from "../promptActions/SaveAndCommit";
import { isContentNotEmpty } from "../Playground/common";

import CompareInputSection from "./CompareInputSection";
import { ChoosePromptTemplateDrawer } from "../../ChoosePromptTemplateDrawer";
import { usePromptStoreShallow } from "src/sections/workbench-v2/store/usePromptStore";
import SavePromptTemplate from "src/sections/workbench-v2/components/SavePromptTemplate";

const CompareInputs = () => {
  const { selectedVersions, setPrompts, promptName } =
    usePromptWorkbenchContext();
  const {
    selectTemplateDrawerOpen,
    setSelectTemplateDrawerOpen,
    setOpenSaveTemplate,
    openSaveTemplate,
  } = usePromptStoreShallow((state) => ({
    selectTemplateDrawerOpen: state.selectTemplateDrawerOpen,
    setSelectTemplateDrawerOpen: state.setSelectTemplateDrawerOpen,
    setOpenSaveTemplate: state.setOpenSaveTemplate,
    openSaveTemplate: state.openSaveTemplate,
  }));

  const [saveCommitOpen, setSaveCommitOpen] = useState(null);

  const [isSync, setIsSync] = useState(false);

  const syncSystemPrompt = useCallback(
    (newVal, skipIndex = null) => {
      if (!isContentNotEmpty(newVal)) {
        return;
      }
      setPrompts((existingPrompts) => {
        return existingPrompts.map((p, versionIndex) => {
          if (skipIndex !== null && skipIndex === versionIndex) {
            return { ...p };
          }
          return {
            ...p,
            prompts: p.prompts.map((eachPrompt) => {
              if (eachPrompt.role === PromptRoles.SYSTEM) {
                return {
                  ...eachPrompt,
                  content: newVal,
                  id: getRandomId(),
                };
              }
              return { ...eachPrompt };
            }),
          };
        });
      }, skipIndex);
    },
    [setPrompts],
  );

  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        gap: 2,
        overflow: "hidden",
        height: "100%",
      }}
    >
      {selectedVersions.map((version, index) => {
        return (
          <CompareInputSection
            key={version.id}
            promptVersion={version}
            index={index}
            setSaveCommitOpen={setSaveCommitOpen}
            isSync={isSync}
            setIsSync={setIsSync}
            syncSystemPrompt={syncSystemPrompt}
          />
        );
      })}
      <SaveAndCommit
        open={Boolean(saveCommitOpen)}
        onClose={() => setSaveCommitOpen(null)}
        data={saveCommitOpen}
        promptName={promptName}
      />
      <SavePromptTemplate
        data={openSaveTemplate}
        open={Boolean(openSaveTemplate)}
        onClose={() => setOpenSaveTemplate(false)}
      />
      <ChoosePromptTemplateDrawer
        open={selectTemplateDrawerOpen}
        onClose={() => setSelectTemplateDrawerOpen(false)}
        importMode
      />
    </Box>
  );
};

export default CompareInputs;
