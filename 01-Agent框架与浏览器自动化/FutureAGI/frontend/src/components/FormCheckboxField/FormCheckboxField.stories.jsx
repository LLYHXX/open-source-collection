import { useForm } from "react-hook-form";
import { FormCheckboxField } from "./FormCheckboxField";
import React from "react";

const meta = {
  component: FormCheckboxField,
  title: "React Hook Form/FormCheckboxField",
};

export default meta;

const Template = (args) => {
  const { control } = useForm();

  return <FormCheckboxField {...args} control={control} fieldName="" />;
};

export const Default = Template.bind({});

Default.args = {
  label: "Checkbox Label",
  labelPlacement: "end",
  helperText: "",
};
