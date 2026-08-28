import { useForm } from "react-hook-form";
import { FormDateField } from "./FormDateField";
import React from "react";

const meta = {
  component: FormDateField,
  title: "React Hook Form/FormDateField",
};

export default meta;

const Template = (args) => {
  const { control } = useForm();

  return <FormDateField {...args} control={control} fieldName="" />;
};

export const Default = Template.bind({});

Default.args = {
  fullWidth: true,
  label: "Date Field Label",
  size: "medium",
};
