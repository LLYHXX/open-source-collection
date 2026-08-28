import React from "react";
import EvalDatasetSelect from "./EvaluationSelect";
import { MemoryRouter } from "react-router-dom";
import logger from "src/utils/logger";

const meta = {
  component: EvalDatasetSelect,
  title: "UI Components/EvalDatasetSelect",
};

export default meta;

const Template = (args) => (
  <MemoryRouter>
    <EvalDatasetSelect {...args} />
  </MemoryRouter>
);

export const Default = Template.bind({});
Default.args = {
  options: [
    { value: "option1", label: "Option 1" },
    { value: "option2", label: "Option 2" },
    { value: "option3", label: "Option 3" },
  ],
  value: "option1",
  setValue: () => logger.debug("setValue called"),
};
