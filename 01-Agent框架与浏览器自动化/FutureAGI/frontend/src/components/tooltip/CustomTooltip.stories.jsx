import { Box } from "@mui/material";
import CustomTooltip from "./CustomTooltip";
import React from "react";

const meta = {
  component: CustomTooltip,
  title: "UI Components/CustomTooltip",
};

export default meta;

const Template = (args) => {
  return <CustomTooltip {...args}></CustomTooltip>;
};

export const Default = Template.bind({});

Default.args = {
  children: (
    <Box
      sx={{
        width: "200px",
        backgroundColor: "lightblue",
        textAlign: "center",
        borderRadius: "30px",
      }}
    >
      Hover Over this
    </Box>
  ),
  title: "Tooltip Title",
  show: true,
};
