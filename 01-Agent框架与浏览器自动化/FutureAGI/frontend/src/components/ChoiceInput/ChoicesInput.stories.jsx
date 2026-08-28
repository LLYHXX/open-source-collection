import React from "react";
import { useForm } from "react-hook-form";
import ChoicesInput from "./ChoicesInput";
import logger from "src/utils/logger";

const meta = {
  component: ChoicesInput,
  title: "UI Components/ChoicesInput",
};

export default meta;

const Template = (args) => {
  const { control, handleSubmit } = useForm();

  const onSubmit = (data) => {
    logger.debug(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <ChoicesInput
        control={control}
        config={{}}
        configKey="choices"
        helperText={args.helperText}
        fieldPrefix="config."
        label={args.label}
      />
      {/* <button type="submit">Submit</button> */}
    </form>
  );
};

export const Default = Template.bind({});
Default.args = {
  helperText: "Helper text for choices input",
  label: "Choices Input",
};
