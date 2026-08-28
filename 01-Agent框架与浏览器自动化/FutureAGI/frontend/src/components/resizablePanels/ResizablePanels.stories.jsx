// ResizablePanels.stories.jsx

import React from "react";
import ResizablePanels from "./ResizablePanels";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import Box from "@mui/material/Box";

// Create a mock theme that includes `whiteScale` used in your component
const theme = createTheme({
  palette: {
    whiteScale: {
      500: "#ccc", // default color, replace with your actual color
    },
  },
});

export default {
  title: "Components/ResizablePanels",
  component: ResizablePanels,
};

const Template = (args) => (
  <ThemeProvider theme={theme}>
    <div
      style={{
        width: "100%",
        height: "400px",
        border: "1px solid var(--border-default)",
      }}
    >
      <ResizablePanels {...args} />
    </div>
  </ThemeProvider>
);

export const Default = Template.bind({});
Default.args = {
  leftPanel: (
    <Box p={2} bgcolor="background.neutral" height="100%">
      Left Panel Content
    </Box>
  ),
  rightPanel: (
    <Box p={2} bgcolor="divider" height="100%">
      Right Panel Content
    </Box>
  ),
  initialLeftWidth: 50,
  minLeftWidth: 20,
  maxLeftWidth: 80,
};
