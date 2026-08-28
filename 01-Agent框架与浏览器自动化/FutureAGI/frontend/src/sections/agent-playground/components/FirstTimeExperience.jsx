import { Box, Stack, Typography } from "@mui/material";
import React, { useState } from "react";
import { useNavigate } from "react-router";
import { useAgentPlaygroundStoreShallow } from "../store";
import { LoadingButton } from "@mui/lab";
import { useCreateGraph } from "../../../api/agent-playground/agent-playground";

const activeButtonVariants = {
  SEE_DEMO_AGENT: "seeDemoAgent",
  START_CREATING: "startCreating",
};

export default function FirstTimeExperience() {
  const [activeButton, setActiveButton] = useState("");
  const { setCurrentAgent } = useAgentPlaygroundStoreShallow((s) => ({
    setCurrentAgent: s.setCurrentAgent,
  }));
  const navigate = useNavigate();

  const { mutate: createDemoAgent, isPending: isCreatingDemoAgent } =
    useCreateGraph({
      navigate,
      setCurrentAgent,
      onSuccess: () => {
        setActiveButton("");
      },
    });

  // const handleSeeDemoAgent = () => {
  //   setActiveButton(activeButtonVariants.SEE_DEMO_AGENT);
  //   createDemoAgent({
  //     demo: true,
  //   });
  // };

  const handleStartCreating = () => {
    setActiveButton(activeButtonVariants.START_CREATING);
    createDemoAgent();
  };

  return (
    <Box
      sx={{
        py: 4,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 4,
      }}
    >
      <Stack alignItems={"center"}>
        <Typography
          typography={"m3"}
          fontWeight={"fontWeightMedium"}
          color={"text.primary"}
        >
          Agent Playground
        </Typography>
        <Typography
          typography={"m3"}
          fontWeight={"fontWeightRegular"}
          color={"text.secondary"}
        >
          Break down complex tasks into sequential steps that build upon each
          other
        </Typography>
      </Stack>
      {/* video section */}
      <Box
        sx={{
          minWidth: "960px",
          maxWidth: "1200px",
          minHeight: "60vh",
          bgcolor: "background.paper",
        }}
      ></Box>
      <Stack gap={1.75} direction={"row"} alignItems={"center"}>
        {/* <LoadingButton
          loading={
            isCreatingDemoAgent &&
            activeButton === activeButtonVariants.SEE_DEMO_AGENT
          }
          onClick={handleSeeDemoAgent}
          size="small"
          variant="outlined"
          color="primary"
        >
          See demo agent
        </LoadingButton> */}
        <LoadingButton
          loading={
            isCreatingDemoAgent &&
            activeButton === activeButtonVariants.START_CREATING
          }
          onClick={handleStartCreating}
          size="small"
          variant="contained"
          color="primary"
        >
          Start creating
        </LoadingButton>
      </Stack>
    </Box>
  );
}
