import React from "react";
import EvaluationTypeCard from "./EvaluationTypeCard";
import logger from "src/utils/logger";

const meta = {
  component: EvaluationTypeCard,
  title: "UI Components/EvaluationTypeCard",
};

export default meta;

const Template = (args) => {
  const handleClick = () => {
    logger.debug("Card clicked");
  };

  return (
    <EvaluationTypeCard
      title="Evaluation Type"
      subTitle="This is a subtitle"
      onClick={handleClick}
      {...args}
    />
  );
};

export const Default = Template.bind({});

Default.args = {
  tags: ["tag1", "tag2", "tag3"],
};
