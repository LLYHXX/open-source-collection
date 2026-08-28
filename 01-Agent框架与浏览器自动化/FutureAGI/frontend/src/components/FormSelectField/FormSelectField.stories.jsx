import { useForm } from "react-hook-form";
import { EnhancedFormSelectField } from "./FormSelectField";
import React from "react";

const meta = {
  component: EnhancedFormSelectField,
  title: "React Hook Form/FormSelectField",
};

export default meta;

const Template = (args) => {
  const { control } = useForm();

  return <EnhancedFormSelectField {...args} control={control} fieldName="" />;
};

export const Default = Template.bind({});

Default.args = {
  label: "Label Text",
  size: "small",
  options: [
    { label: "Option 1", value: "Value 1" },
    { label: "Option 2", value: "Value 2" },
  ],
  control: {},
  fieldName: "",
  fullWidth: true,
  isSearchable: false,
  valueSelector: () => {},
  helperText: "Helper Text",
  dropDownMaxHeight: 200,
  onScrollEnd: () => {},
  loadingMoreOptions: false,
  allowClear: false,
};
