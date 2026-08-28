import { Box, Typography, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import React, { useMemo } from "react";
import {
  CustomTab,
  CustomTabs,
  TabWrapper,
} from "src/sections/develop/AddDatasetDrawer/AddDatasetStyle";
import { tabOptions } from "./constant";
import { ShowComponent } from "../show";
import SvgColor from "../svg-color";

const FieldHeader = ({
  fieldTitle,
  currentTab,
  setCurrentTab,
  showTabs,
  type,
  hideAudio,
  required,
  errorMessage,
}) => {
  const theme = useTheme();

  const filterOption = useMemo(() => {
    const filtered = tabOptions.filter((item) =>
      item.value == "audio" && hideAudio ? false : true,
    );
    if (filtered.some((item) => item.value !== currentTab)) {
      setCurrentTab("text");
    }
    return filtered;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hideAudio]);

  return (
    <Box sx={{ display: "flex", justifyContent: "space-between" }}>
      <Typography
        typography="s1"
        fontWeight="fontWeightMedium"
        color={errorMessage ? "error.main" : "text.primary"}
        display={"flex"}
        alignItems={"center"}
        gap={0.5}
      >
        {type === "image" && (
          <SvgColor
            src="/assets/icons/ic_image.svg"
            sx={{
              color: errorMessage ? "error.main" : "text.disabled",
              width: "16px",
              height: "16px",
            }}
          />
        )}
        {type === "audio" && (
          <SvgColor
            src="/assets/icons/ic_audio.svg"
            sx={{
              color: errorMessage ? "error.main" : "text.disabled",
              width: "16px",
              height: "16px",
            }}
          />
        )}
        {type === "text" && (
          <SvgColor
            src="/assets/icons/navbar/ic_new_text.svg"
            sx={{
              color: errorMessage ? "error.main" : "text.disabled",
              width: "16px",
              height: "16px",
            }}
          />
        )}
        {fieldTitle}
        {required && <span style={{ color: "red" }}>*</span>}
      </Typography>
      <ShowComponent condition={showTabs}>
        <TabWrapper
          sx={{ backgroundColor: "action.hover", marginBottom: "0px" }}
        >
          <CustomTabs
            value={currentTab}
            onChange={(e, value) => setCurrentTab(value)}
            sx={{
              "& .Mui-selected": {
                backgroundColor: `${theme.palette.background.paper}`,
                borderRadius: 0.75,
                color: (theme) => `${theme.palette.text.primary} !important`,
              },
            }}
            TabIndicatorProps={{
              style: {
                backgroundColor: `${theme.palette.background.paper}`,
                opacity: 0.08,
                height: "100%",
                borderRadius: 1,
              },
            }}
          >
            {filterOption.map((tab) => (
              <CustomTab
                key={tab.value}
                label={tab.label}
                value={tab.value}
                disabled={tab.disabled}
                sx={{
                  fontWeight: theme.typography.fontWeightMedium,
                  color: (theme) => `${theme.palette.text.disabled} !important`,
                }}
              />
            ))}
          </CustomTabs>
        </TabWrapper>
      </ShowComponent>
    </Box>
  );
};

FieldHeader.propTypes = {
  fieldTitle: PropTypes.string,
  currentTab: PropTypes.string,
  setCurrentTab: PropTypes.func,
  showTabs: PropTypes.bool,
  type: PropTypes.string,
  hideAudio: PropTypes.bool,
  required: PropTypes.bool,
  errorMessage: PropTypes.string,
};

export default FieldHeader;
