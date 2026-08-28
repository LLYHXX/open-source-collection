import React from "react";
import { PromptSection } from "./PromptSection";
import { useForm } from "react-hook-form";
import { Box } from "@mui/material";
import { logger } from "@sentry/react";

export default {
  title: "Components/PromptSection",
  component: PromptSection,
};

const Template = (args) => {
  const { control } = useForm();

  return (
    <Box sx={{ width: "100%" }}>
      <PromptSection {...args} control={control} />
    </Box>
  );
};

export const Default = Template.bind({});

Default.args = {
  allColumns: [
    { headerName: "Column 1", value: "Value 1" },
    { headerName: "Column 2", value: "Value 2" },
    { headerName: "Column 3", value: "Value 3" },
  ],
  prefixControlString: "",
  contentSuffix: "content",
  roleSuffix: "role",
  onRemove: () => logger.debug("Remove clicked"),
  roleSelectDisabled: false,
};

export const WithRoleSelectDisabled = Template.bind({});

WithRoleSelectDisabled.args = {
  allColumns: [
    { headerName: "Column 1", value: "Value 1" },
    { headerName: "Column 2", value: "Value 2" },
    { headerName: "Column 3", value: "Value 3" },
  ],
  prefixControlString: "",
  contentSuffix: "content",
  roleSuffix: "role",
  onRemove: () => logger.debug("Remove clicked"),
  roleSelectDisabled: true,
  hideSelectRole: false,
};

export const WithHideRoleSelect = Template.bind({});

WithHideRoleSelect.args = {
  allColumns: [
    { headerName: "Column 1", value: "Value 1" },
    { headerName: "Column 2", value: "Value 2" },
    { headerName: "Column 3", value: "Value 3" },
  ],
  prefixControlString: "",
  contentSuffix: "content",
  roleSuffix: "role",
  onRemove: () => logger.debug("Remove clicked"),
  roleSelectDisabled: false,
  hideSelectRole: true,
};
