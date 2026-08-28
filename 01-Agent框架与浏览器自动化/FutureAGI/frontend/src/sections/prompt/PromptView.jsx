import React, { useState } from "react";
import { Box } from "@mui/material";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

import PromptRightSidebar from "./PromtSidebar/PromptRightSidebar";
import PromtLeftSidebar from "./PromtSidebar/PromtLeftSidebar";

const PromptView = () => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");

  const deletePrompt = useMutation({
    mutationFn: (id) =>
      axios.delete(endpoints.develop.runPrompt.promptDelete(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["prompts"],
      });
    },
  });

  const handleDelete = (id) => {
    deletePrompt.mutate(id);
  };

  return (
    <Box
      sx={{
        backgroundColor: "background.paper",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        gap: 2,
        flex: 1,
        overflow: "hidden",
      }}
    >
      <Box
        sx={{
          display: "flex",
          height: "100%",
        }}
      >
        <Box
          sx={{
            borderRight: 3,
            borderRightStyle: "solid",
            borderRightColor: "divider",
            padding: "12px 0 36px 0",
            display: "flex",
            flexDirection: "column",
            height: "100%",
            maxWidth: "274px",
            minWidth: "274px",
            flex: "1",
          }}
        >
          <PromtLeftSidebar
            setCurrentIndex={() => {}}
            closeSidebar={() => {}}
            onDelete={handleDelete}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
          />
        </Box>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flex: "1",
            height: "100%",
            overflow: "auto",
            padding: "0 12px",
          }}
        >
          <PromptRightSidebar />
        </Box>
      </Box>
    </Box>
  );
};

export default PromptView;
