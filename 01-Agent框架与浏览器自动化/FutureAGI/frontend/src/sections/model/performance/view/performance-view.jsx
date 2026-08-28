import PropTypes from "prop-types";
import { Box, ToggleButton, ToggleButtonGroup } from "@mui/material";
import React, { useState } from "react";
import Iconify from "src/components/iconify";
import ModelDataset from "../model-dataset";
import ModelPerformance from "../model-performance";
import DatasetDrift from "../dataset-drift";
import EmbeddingInsights from "../embedding-insights";
import DatasetImportance from "../dataset-importance";

export default function PerformanceView({ model }) {
  const [currentTab, setCurrentTab] = useState("modelPerformance");

  const TABS = [
    {
      value: "modelPerformance",
      label: "Performance",
      icon: <Iconify icon="solar:user-id-bold" width={24} />,
    },
    {
      value: "drift",
      label: "Drift",
      icon: <Iconify icon="solar:user-id-bold" width={24} />,
    },
    {
      value: "embedding",
      label: "Embedding",
      icon: <Iconify icon="solar:user-id-bold" width={24} />,
    },
    {
      value: "explainability",
      label: "Explainability",
      icon: <Iconify icon="solar:user-id-bold" width={24} />,
    },
    // {
    //   value: "fairness",
    //   label: "Fairness",
    //   icon: <Iconify icon="solar:user-id-bold" width={24} />,
    // },
    {
      value: "dataset",
      label: "Datasets",
      icon: <Iconify icon="solar:user-id-bold" width={24} />,
    },
  ];

  const handleAlignment = (event, newAlignment) => {
    setCurrentTab(newAlignment);
  };

  return (
    <Box>
      <ToggleButtonGroup
        value={currentTab}
        exclusive
        onChange={handleAlignment}
        aria-label="text alignment"
        size="small"
      >
        {TABS.map((tab) => (
          <ToggleButton
            key={tab.value}
            value={tab.value}
            aria-label={tab.label}
          >
            {tab.icon}
            {tab.label}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>

      {currentTab === "modelPerformance" && <ModelPerformance model={model} />}
      {currentTab === "drift" && <DatasetDrift model={model} />}
      {currentTab === "dataset" && <ModelDataset model={model} />}
      {currentTab === "embedding" && <EmbeddingInsights model={model} />}
      {currentTab === "explainability" && <DatasetImportance model={model} />}
    </Box>
  );
}

PerformanceView.propTypes = {
  model: PropTypes.object,
};
