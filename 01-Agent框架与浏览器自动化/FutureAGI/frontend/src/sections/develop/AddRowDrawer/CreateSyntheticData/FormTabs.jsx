import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import Iconify from "src/components/iconify";

const tabTextColor = {
  completed: "green.500",
  active: "blue.500",
  pending: "text.secondary",
};
const tabBackgroundColor = {
  completed: "green.o10",
  active: "blue.o10",
  pending: "background.neutral",
};
const tabBorderColor = {
  completed: "green.500",
  active: "blue.500",
  pending: "divider",
};

const FormTabs = ({ tabList, handleTabChange }) => {
  return (
    <Box sx={{ display: "flex", gap: 1 }}>
      {tabList.map((item, index) => {
        const { label, value, status } = item;
        return (
          <Box
            key={value}
            sx={{
              flex: 1,
              padding: "4px",
              gap: 1,
              display: "flex",
              alignItems: "center",
              borderRadius: "4px",
              border: "1px solid",
              cursor: "pointer",
              borderColor: tabBorderColor[status],
            }}
            onClick={() => handleTabChange(index)}
          >
            <Box
              sx={{
                backgroundColor: tabBackgroundColor[status],
                color: tabTextColor[status],
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                width: "28px",
                height: "28px",
                borderRadius: "2px",
              }}
            >
              {status === "completed" ? (
                <Iconify icon="qlementine-icons:success-16" color="green.700" />
              ) : (
                index + 1
              )}
            </Box>
            <Typography
              variant="s2"
              fontWeight={
                status === "active" ? "fontWeightMedium" : "fontWeightRegular"
              }
              color="text.primary"
            >
              {label}
            </Typography>
          </Box>
        );
      })}
    </Box>
  );
};

export default FormTabs;

FormTabs.propTypes = {
  tabList: PropTypes.array,
  handleTabChange: PropTypes.func,
};
