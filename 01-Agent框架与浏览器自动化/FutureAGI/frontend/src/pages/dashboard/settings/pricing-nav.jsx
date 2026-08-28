import React, { useCallback } from "react";
import PropTypes from "prop-types";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { Tab, Tabs, useTheme } from "@mui/material";

const PricingNavComponent = ({ tabs, currentTab, onTabChange }) => {
  const theme = useTheme();

  const handleTabChange = useCallback(
    (event, newTabPath) => {
      onTabChange(event, newTabPath);
    },
    [onTabChange],
  );

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: theme.spacing(2),
      }}
    >
      <Typography
        variant="m2"
        color="text.primary"
        fontWeight="fontWeightSemiBold"
      >
        Settings
      </Typography>
      <Box
        sx={{
          borderBottom: 1,
          borderColor: "divider",
          width: "100%",
        }}
      >
        <Tabs
          value={currentTab?.path || tabs[0]?.path}
          onChange={handleTabChange}
          textColor="primary"
          TabIndicatorProps={{
            style: {
              backgroundColor: theme.palette.primary.main,
            },
          }}
          sx={{
            minHeight: 48,
            "& .MuiTabs-flexContainer": {
              gap: 0,
            },
            "& .MuiTab-root": {
              minHeight: 48,
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
              "&:first-of-type": {
                marginLeft: 0,
              },
            },
          }}
        >
          {tabs.map((tab) => (
            <Tab
              key={tab.path}
              label={tab.title}
              icon={tab.icon}
              value={tab.path}
            />
          ))}
        </Tabs>
      </Box>
    </Box>
  );
};

PricingNavComponent.propTypes = {
  tabs: PropTypes.arrayOf(
    PropTypes.shape({
      path: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      icon: PropTypes.element.isRequired,
    }),
  ).isRequired,
  currentTab: PropTypes.shape({
    path: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    icon: PropTypes.element.isRequired,
  }),
  onTabChange: PropTypes.func.isRequired,
};

const PricingNav = React.memo(PricingNavComponent);
PricingNav.displayName = "PricingNav";

export default PricingNav;
