import React, { useRef, useState } from "react";
import PropTypes from "prop-types";
import { Box, Button, Tab, Tabs, useTheme } from "@mui/material";
import { ShowComponent } from "src/components/show";
import TestExecutionSelectionPopover from "./TestExecutionSelectionPopover";
import { useSelectedExecutionsStoreShallow } from "./states";

const TestDetailTabsComponent = ({ tabs, currentTab, onTabChange }) => {
  const theme = useTheme();
  const [open, setOpen] = useState(false);
  const anchorRef = useRef(null);
  const selectedExecutions = useSelectedExecutionsStoreShallow(
    (s) => s.selectedExecutions,
  );
  // Get all tabs with icons from navData

  const handleTabChange = React.useCallback(
    (event, newTabId) => {
      onTabChange(event, newTabId);
    },
    [onTabChange],
  );

  return (
    <Box
      sx={{
        borderBottom: 1,
        borderColor: "divider",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 1,
      }}
    >
      <Tabs
        value={currentTab?.id || tabs[0]?.id}
        onChange={handleTabChange}
        textColor="primary"
        TabIndicatorProps={{
          style: {
            backgroundColor: theme.palette.primary.main,
          },
        }}
        sx={{
          minHeight: 42,
          "& .MuiTabs-flexContainer": {
            gap: 0,
          },
          "& .MuiTab-root": {
            minHeight: 42,
            paddingX: theme.spacing(1.5),
            margin: theme.spacing(0),
            marginRight: theme.spacing(0) + "!important",
            minWidth: "auto",
            fontWeight: "fontWeightMedium",
            typography: "s1",
            color: "text.disabled",
            textTransform: "none",
            transition: theme.transitions.create(
              ["color", "background-color"],
              {
                duration: theme.transitions.duration.short,
              },
            ),
            "&.Mui-selected": {
              color: "primary.main",
              fontWeight: "fontWeightSemiBold",
            },
            "&:not(.Mui-selected)": {
              color: `${theme.palette.text.disabled}`,
            },
            "&:first-of-type": {
              marginLeft: 0,
            },
          },
        }}
      >
        {tabs.map((tab) => {
          return (
            <Tab
              key={tab.id}
              label={tab.title}
              value={tab.id}
              icon={tab?.icon}
            />
          );
        })}
      </Tabs>
      <ShowComponent condition={currentTab?.id === "analytics"}>
        <Button
          variant="outlined"
          size="small"
          ref={anchorRef}
          onClick={() => {
            setOpen(true);
          }}
        >
          Executions ({selectedExecutions.length})
        </Button>
        <TestExecutionSelectionPopover
          open={open}
          onClose={() => setOpen(false)}
          anchor={anchorRef.current}
        />
      </ShowComponent>
    </Box>
  );
};

TestDetailTabsComponent.propTypes = {
  tabs: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      path: PropTypes.string.isRequired,
    }),
  ).isRequired,
  currentTab: PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    path: PropTypes.string.isRequired,
  }),
  onTabChange: PropTypes.func.isRequired,
};

const TestDetailTabs = React.memo(TestDetailTabsComponent);
TestDetailTabs.displayName = "TestDetailTabs";

export default TestDetailTabs;
