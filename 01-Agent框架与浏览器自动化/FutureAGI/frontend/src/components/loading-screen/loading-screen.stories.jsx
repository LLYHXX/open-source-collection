import React from "react";
import LoadingScreen from "./loading-screen";

export default {
  title: "Components/LoadingScreen",
  component: LoadingScreen,
  parameters: {
    layout: "centered",
  },
};

// Default loading screen
export const Default = {
  args: {},
};

// Custom width loading screen
export const CustomWidth = {
  args: {
    sx: {
      maxWidth: 200,
    },
  },
};

// Custom color loading screen
export const CustomColor = {
  args: {
    sx: {
      "& .MuiLinearProgress-root": {
        backgroundColor: "var(--border-default)",
        "& .MuiLinearProgress-bar": {
          backgroundColor: "#2196f3",
        },
      },
    },
  },
};

// Full width loading screen
export const FullWidth = {
  args: {
    sx: {
      width: "100vw",
      maxWidth: "none",
    },
  },
};
