import { Box } from "@mui/material";
import React, { useRef, useState } from "react";
import PageHeadings from "../develop-detail/Common/PageHeadings";
import HelpKnowledgeBase from "./help/HelpKnowledgeBase";
import InfoKnowledgeModal from "./help/InfoKnowledgeModal";
import CreateKnowledgeBaseDrawer from "./CreateKnowledgeBase/CreateKnowledgeBaseDrawer";
import KnowledgeBaseData from "./KnowledgeBaseData/KnowledgeBaseData";

const KnowledgeBaseView = () => {
  const [createKnowledgeBase, setCreateKnowledgeBase] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [hasData, setHasData] = useState(true);
  const gridRef = useRef();

  return (
    <Box
      sx={{
        backgroundColor: "background.paper",
        height: "100%",
        padding: 2,
        display: "flex",
        flexDirection: "column",
        gap: 3,
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
        }}
      >
        <PageHeadings
          title="Create Knowledge Base"
          description="Provide domain-specific information to help agent behaviour as per your business use-case"
        />
      </Box>
      <Box sx={{ display: hasData ? "block" : "none", flex: 1 }}>
        <KnowledgeBaseData
          setHasData={setHasData}
          setShowHelp={setShowHelp}
          setCreateKnowledgeBase={setCreateKnowledgeBase}
          ref={gridRef}
        />
      </Box>
      <Box sx={{ display: hasData ? "none" : "block", flex: 1 }}>
        <HelpKnowledgeBase
          onCreateKnowledge={() => setCreateKnowledgeBase(true)}
        />
      </Box>
      <CreateKnowledgeBaseDrawer
        open={createKnowledgeBase}
        onClose={() => setCreateKnowledgeBase(false)}
        setHasData={setHasData}
        refreshGrid={() => gridRef?.current?.api?.refreshServerSide({})}
      />
      <InfoKnowledgeModal
        open={showHelp && !createKnowledgeBase}
        onClose={() => setShowHelp(false)}
        onCreateKnowledge={() => {
          setCreateKnowledgeBase(true);
          setShowHelp(false);
        }}
      />
    </Box>
  );
};

export default KnowledgeBaseView;
