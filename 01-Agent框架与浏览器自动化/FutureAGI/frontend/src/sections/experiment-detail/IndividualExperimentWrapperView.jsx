import { Box } from "@mui/material";
import React from "react";
import { Outlet, useLocation } from "react-router";
import ExperimentDetailContextProvider from "./ExperimentContextProvider";
import IndividualExperimentBarSummaryRightSection from "./IndividualExperimentBarRightSection/IndividualExperimentBarSummaryRightSection";
import IndividualExperimentBarDataRightSection from "./IndividualExperimentBarRightSection/IndividualExperimentBarDataRightSection";
import IndividualExperimentRow from "./IndividualExperimentRow";
import IndividualExperimentBar from "./IndividualExperimentBar";

const IndividualExperimentWrapperView = () => {
  const location = useLocation();
  const currentTab = location.pathname.split("/").pop();

  const renderRightSection = () => {
    if (currentTab === "data") {
      return <IndividualExperimentBarDataRightSection />;
    } else if (currentTab === "summary") {
      return <IndividualExperimentBarSummaryRightSection />;
    }
  };

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
        <IndividualExperimentRow />
        <IndividualExperimentBar rightSection={renderRightSection()} />
        <Outlet />
      </Box>
    </ExperimentDetailContextProvider>
  );
};

export default IndividualExperimentWrapperView;
