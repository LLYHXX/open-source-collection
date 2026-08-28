import PropTypes from "prop-types";
import { Box, ToggleButton, ToggleButtonGroup } from "@mui/material";
import React, { useState } from "react";
import Iconify from "src/components/iconify";

import ModelInsights from "../model-insights";
import ModelEvents from "../model-events";
import ModelFunnel from "../model-funnel";

export default function JourneyView({ modelId }) {
  const TABS = [
    {
      value: "events",
      label: "Events",
      icon: <Iconify icon="solar:user-id-bold" width={24} />,
    },
    {
      value: "insights",
      label: "Insights",
      icon: <Iconify icon="solar:user-id-bold" width={24} />,
    },
    {
      value: "funnel",
      label: "Funnel",
      icon: <Iconify icon="solar:user-id-bold" width={24} />,
    },
  ];

  const handleAlignment = (event, newAlignment) => {
    setSelectedTab(newAlignment);
  };

  const [selectedTab, setSelectedTab] = useState(TABS[0].value);

  return (
    <Box>
      <ToggleButtonGroup
        value={selectedTab}
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

      {selectedTab === "events" && <ModelEvents modelId={modelId} />}
      {selectedTab === "insights" && <ModelInsights modelId={modelId} />}
      {selectedTab === "funnel" && <ModelFunnel modelId={modelId} />}
    </Box>
  );
}

JourneyView.propTypes = {
  modelId: PropTypes.string,
};
