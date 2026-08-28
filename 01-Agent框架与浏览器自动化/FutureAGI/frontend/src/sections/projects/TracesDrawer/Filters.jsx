import { Stack, tabClasses, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import {
  CustomTab,
  CustomTabs,
  TabWrapper,
} from "src/sections/develop/AddDatasetDrawer/AddDatasetStyle";

const tabOptions = [
  { label: "Markdown", value: "markdown", disabled: false },
  { label: "Raw", value: "raw", disabled: false },
];

export default function Filters({ viewType, setViewType }) {
  const theme = useTheme();
  return (
    <Stack
      direction={"row"}
      alignItems={"center"}
      justifyContent={"space-between"}
    >
      <TabWrapper
        sx={{
          marginBottom: 0,
          width: "max-content",
          border: "none",
          padding: 0,
        }}
      >
        <CustomTabs
          value={viewType}
          onChange={(e, value) => setViewType(value)}
          TabIndicatorProps={{
            style: {
              backgroundColor: "transparent", // disable default indicator
            },
          }}
          sx={{
            backgroundColor: theme.palette.background.default,
            borderRadius: "4px",
            p: "4px",
            minHeight: "unset",
            [`& .${tabClasses.root}`]: {
              borderRadius: "4px",
              textTransform: "none",
              minHeight: "unset",
              padding: "1px 7px 3px",
              transition: "all 0.2s ease-in-out",
              color: "text.disabled",
            },
            [`& .${tabClasses.selected}`]: {
              backgroundColor: theme.palette.background.paper,
              boxShadow:
                "0px 2px 6px rgba(0, 0, 0, 0.08), 0px 1px 2px rgba(0, 0, 0, 0.04)",
              color: "text.primary",
              fontWeight: 500,
            },
            [`& .${tabClasses.root}:not(.${tabClasses.selected})`]: {
              color: theme.palette.text.secondary,
            },
          }}
        >
          {tabOptions.map((tab) => (
            <CustomTab
              key={tab.value}
              label={tab.label}
              value={tab.value}
              disabled={tab.disabled}
            />
          ))}
        </CustomTabs>
      </TabWrapper>
      {/* <FormSearchField
        size="small"
        placeholder="Search"
        disableUnderline
        searchQuery={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        sx={{
          width: "279px",
        }}
      /> */}
    </Stack>
  );
}

Filters.propTypes = {
  viewType: PropTypes.string,
  setViewType: PropTypes.func,
};
