import { Box, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import React, { useMemo } from "react";
import CustomTooltip from "src/components/tooltip";
import {
  CustomTab,
  CustomTabs,
  TabWrapper,
} from "src/sections/develop/AddDatasetDrawer/AddDatasetStyle";

// eslint-disable-next-line react-refresh/only-export-components
export const CONTAINER_SMALL =
  "@container (min-width: 350px) and (max-width: 750px)";
// eslint-disable-next-line react-refresh/only-export-components
export const CONTAINER_XS = "@container (max-width: 349px)";

const CustomAgentTabs = ({
  value,
  onChange,
  tabs,
  containerResponsive = false,
}) => {
  const theme = useTheme();

  const tabWrapperStyles = useMemo(
    () => ({
      alignSelf: "flex-start",
      backgroundColor: "action.hover",
      border: 0,
      padding: theme.spacing(0),
      borderRadius: "4px",
      position: "relative",
      marginBottom: "0px",
      ...(containerResponsive && {
        [CONTAINER_SMALL]: {
          alignSelf: "stretch",
          width: "100%",
        },
      }),
    }),
    [theme, containerResponsive],
  );

  const tabStyles = useMemo(
    () => ({
      paddingTop: theme.spacing(0.5),
      paddingBottom: theme.spacing(0.5),
      margin: theme.spacing(0.5),
      borderRadius: "4px",
      position: "relative",
      fontWeight: 500,
      minHeight: "auto",
      color: theme.palette.text.disabled,
      "&.Mui-selected": {
        backgroundColor: "var(--bg-paper) !important",
        boxShadow: "3px 3px 6px rgba(0, 0, 0, 0.12)",
        color: "text.primary",
      },
      ...(containerResponsive && {
        [CONTAINER_SMALL]: {
          flex: 1,
        },
      }),
    }),
    [theme, containerResponsive],
  );

  const outerSx = useMemo(() => {
    if (containerResponsive)
      return {
        maxWidth: "100%",
        [CONTAINER_SMALL]: { width: "100%" },
      };
    return {};
  }, [containerResponsive]);

  return (
    <Box sx={outerSx}>
      <TabWrapper sx={tabWrapperStyles}>
        <CustomTabs
          value={value}
          onChange={onChange}
          TabIndicatorProps={{ style: { display: "none" } }}
          sx={{
            minHeight: "auto",
            "& .MuiTabs-flexContainer": {
              gap: theme.spacing(0.25),
            },
            ...(containerResponsive && {
              [CONTAINER_SMALL]: {
                width: "100%",
                "& .MuiTabs-flexContainer": {
                  width: "100%",
                },
              },
            }),
          }}
        >
          {tabs.map((tab) => {
            const tabElement = (
              <CustomTab
                key={tab.value}
                label={tab.label}
                value={tab.value}
                disabled={tab.disabled}
                sx={tabStyles}
              />
            );

            return tab.disabled ? (
              <CustomTooltip
                key={tab.value}
                title="Not available yet"
                show
                size="small"
                arrow
                placement="top"
              >
                <Box>{tabElement}</Box>
              </CustomTooltip>
            ) : (
              tabElement
            );
          })}
        </CustomTabs>
      </TabWrapper>
    </Box>
  );
};

CustomAgentTabs.propTypes = {
  value: PropTypes.string,
  onChange: PropTypes.func,
  tabs: PropTypes.array,
  containerResponsive: PropTypes.bool,
};

export default CustomAgentTabs;
