// FormSearchSelectFieldState.stories.jsx

import React, { useState } from "react";
import { Box } from "@mui/material";
import FormSearchSelectFieldState from "./FormSearchSelectFieldState";

// Example options for the select field
const options = [
  { label: "Apple", value: "apple" },
  { label: "Banana", value: "banana" },
  { label: "Cherry", value: "cherry" },
  { label: "Durian", value: "durian", disabled: true },
  { label: "Elderberry", value: "elderberry" },
];

export default {
  title: "Components/FormSearchSelectFieldState",
  component: FormSearchSelectFieldState,
  argTypes: {
    label: { control: "text" },
    value: { control: "text" },
    sx: { control: "object" },
  },
};

const Template = (args) => {
  const [value, setValue] = useState(args.value || "");

  return (
    <Box sx={{ width: 320 }}>
      <FormSearchSelectFieldState
        {...args}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        options={args.options || options}
      />
    </Box>
  );
};

export const Default = Template.bind({});
Default.args = {
  label: "Select Fruit",
  value: "",
  options,
};

export const WithPreselectedValue = Template.bind({});
WithPreselectedValue.args = {
  label: "Select Fruit",
  value: "banana",
  options,
};

export const DisabledOption = Template.bind({});
DisabledOption.args = {
  label: "Select Fruit",
  value: "",
  options,
};

export const CustomStyling = Template.bind({});
CustomStyling.args = {
  label: "Custom Styled",
  value: "",
  options,
  sx: {
    "& .MuiOutlinedInput-root": {
      backgroundColor: "#f0f4ff",
    },
  },
};
