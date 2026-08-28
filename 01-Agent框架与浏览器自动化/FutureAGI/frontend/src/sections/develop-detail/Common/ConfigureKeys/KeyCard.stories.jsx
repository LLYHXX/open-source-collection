import React from "react";
import KeyCard from "./KeyCard";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import logger from "src/utils/logger";

const queryClient = new QueryClient();

const meta = {
  component: KeyCard,
  title: "UI Components/KeyCard",
};

export default meta;

const Template = (args) => {
  const [isFetching] = React.useState(false);

  const handleClose = () => {
    logger.debug("Close button clicked");
  };

  const data = {
    hasKey: true,
    maskedKey: "masked-key",
    provider: "provider",
    logoUrl: "https://example.com/logo.png",
    display_name: "Display Name",
  };

  return (
    <QueryClientProvider client={queryClient}>
      <KeyCard
        data={data}
        isFetching={isFetching}
        onClose={handleClose}
        {...args}
      />
    </QueryClientProvider>
  );
};

export const Default = Template.bind({});

Default.args = {};

export const WithLoading = Template.bind({});

WithLoading.args = {
  isFetching: true,
};

export const WithoutKey = Template.bind({});

WithoutKey.args = {
  data: {
    hasKey: false,
    maskedKey: "",
    provider: "provider",
    logoUrl: "https://example.com/logo.png",
    display_name: "Display Name",
  },
};

export const WithDifferentProvider = Template.bind({});

WithDifferentProvider.args = {
  data: {
    hasKey: true,
    maskedKey: "masked-key",
    provider: "different-provider",
    logoUrl: "https://example.com/logo.png",
    display_name: "Display Name",
  },
};
