import React from "react";
import IncrementerButton from "./IncrementerButton";
import logger from "src/utils/logger";

const meta = {
  component: IncrementerButton,
  title: "UI Components/IncrementerButton",
};

export default meta;

const Template = (args) => <IncrementerButton {...args} />;

export const Default = Template.bind({});
Default.args = {
  quantity: 5,
  onIncrease: () => logger.debug("Increase button clicked"),
  onDecrease: () => logger.debug("Decrease button clicked"),
  disabledIncrease: false,
  disabledDecrease: false,
};

export const DisabledIncrease = Template.bind({});
DisabledIncrease.args = {
  quantity: 5,
  onIncrease: () => logger.debug("Increase button clicked"),
  onDecrease: () => logger.debug("Decrease button clicked"),
  disabledIncrease: true,
  disabledDecrease: false,
};

export const DisabledDecrease = Template.bind({});
DisabledDecrease.args = {
  quantity: 5,
  onIncrease: () => logger.debug("Increase button clicked"),
  onDecrease: () => logger.debug("Decrease button clicked"),
  disabledIncrease: false,
  disabledDecrease: true,
};

export const DisabledBoth = Template.bind({});
DisabledBoth.args = {
  quantity: 5,
  onIncrease: () => logger.debug("Increase button clicked"),
  onDecrease: () => logger.debug("Decrease button clicked"),
  disabledIncrease: true,
  disabledDecrease: true,
};

export const CustomQuantity = Template.bind({});
CustomQuantity.args = {
  quantity: 10,
  onIncrease: () => logger.debug("Increase button clicked"),
  onDecrease: () => logger.debug("Decrease button clicked"),
  disabledIncrease: false,
  disabledDecrease: false,
};
