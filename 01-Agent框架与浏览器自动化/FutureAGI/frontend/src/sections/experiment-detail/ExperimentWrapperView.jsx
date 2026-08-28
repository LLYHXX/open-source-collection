import { Box } from "@mui/material";
import React from "react";
import ExperimentRow from "./ExperimentRow";
import ExperimentBar from "./ExperimentBar";
import { Outlet } from "react-router";
import ExperimentDetailContextProvider from "./ExperimentContextProvider";

const ExperimentWrapperView = () => {
  return (
    <ExperimentDetailContextProvider>
      <Box
        sx={{
          backgroundColor: "background.paper",
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: 1,
        }}
      >
        <ExperimentRow />
        <ExperimentBar />
        <Outlet />
      </Box>
    </ExperimentDetailContextProvider>
  );
};

export default ExperimentWrapperView;
