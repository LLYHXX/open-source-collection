import React from "react";
import CustomModelDropdown from "./CustomModelDropdown";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import logger from "src/utils/logger";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

export default {
  title: "Components/CustomModelDropdown",
  component: CustomModelDropdown,
  parameters: {
    layout: "centered",
  },
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <Story />
      </QueryClientProvider>
    ),
  ],
};

// Basic dropdown with button
export const BasicButton = {
  args: {
    buttonTitle: "Select Model",
    onChange: (e) => logger.debug("Selected:", e.target.value),
    value: "",
    modelDetail: {},
  },
};

// Search dropdown
export const SearchDropdown = {
  args: {
    searchDropdown: true,
    onChange: (e) => logger.debug("Selected:", e.target.value),
    value: "",
    modelDetail: {},
  },
};

// Pre-selected model
export const PreSelected = {
  args: {
    buttonTitle: "Selected Model",
    onChange: (e) => logger.debug("Selected:", e.target.value),
    value: "gpt-4",
    modelDetail: {
      modelName: "GPT-4",
      providers: "OpenAI",
      isAvailable: true,
      logoUrl: "https://example.com/logo.png",
    },
  },
};

// Disabled state
export const Disabled = {
  args: {
    buttonTitle: "Select Model",
    onChange: (e) => logger.debug("Selected:", e.target.value),
    value: "",
    modelDetail: {},
    disabledClick: true,
    disabledHover: true,
  },
};

// Custom hover placement
export const CustomHover = {
  args: {
    buttonTitle: "Select Model",
    onChange: (e) => logger.debug("Selected:", e.target.value),
    value: "",
    modelDetail: {},
    hoverPlacement: "right",
  },
};

// With custom button icon
export const WithIcon = {
  args: {
    buttonTitle: "Select Model",
    buttonIcon: "solar:bot-bold",
    onChange: (e) => logger.debug("Selected:", e.target.value),
    value: "",
    modelDetail: {},
  },
};
