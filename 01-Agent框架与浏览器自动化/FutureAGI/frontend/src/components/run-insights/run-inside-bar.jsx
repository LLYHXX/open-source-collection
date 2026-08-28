import { Box, Tab, Tabs, useTheme } from "@mui/material";
import React from "react";

import PropTypes from "prop-types";
import { Events, trackEvent } from "src/utils/Mixpanel";

const TabOptions = [
  { label: "Trace", value: "Traces", disabled: false },
  { label: "Spans", value: "Spans", disabled: false },
];

const RunInsideBar = ({ currentTab, setCurrentTab, rightSection }) => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        borderBottom: 1,
        borderColor: "divider",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      <Box>
        <Tabs
          textColor="primary"
          value={currentTab}
          onChange={(e, value) => {
            setCurrentTab(value);
            trackEvent(Events.spanTracesToggle);
          }}
          TabIndicatorProps={{
            style: {
              backgroundColor: theme.palette.primary.main,
            },
          }}
          sx={{
            minHeight: 0,
            "& .MuiTab-root": {
              margin: "0 !important",
              fontWeight: "600",
              typography: "s1",
              color: "primary.main",
              "&:not(.Mui-selected)": {
                color: "text.disabled",
                fontWeight: "500",
              },
            },
          }}
        >
          {TabOptions.map((tab) => (
            <Tab
              key={tab.value}
              label={tab.label}
              value={tab.value}
              disabled={tab.disabled}
              sx={{
                margin: theme.spacing(0),
                px: theme.spacing(1.875),
              }}
            />
          ))}
        </Tabs>
      </Box>
      {rightSection}
    </Box>
  );
};

RunInsideBar.propTypes = {
  currentTab: PropTypes.string,
  setCurrentTab: PropTypes.func,
  rightSection: PropTypes.any,
};

export default RunInsideBar;
