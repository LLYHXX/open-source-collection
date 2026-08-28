import React from "react";
import SliderRow from "./SliderRow";
import { useForm } from "react-hook-form";

const meta = {
  component: SliderRow,
  title: "Components/CustomModelOptions/SliderRow",
};

export default meta;

const Template = (args) => {
  const { control } = useForm();

  return <SliderRow {...args} control={control} fieldName="sliderValue" />;
};

export const Default = Template.bind({});

Default.args = {
  label: "Label Text",
  min: 0,
  max: 1,
  step: 0.1,
  sliderValue: 0.5,
};

export const WithCustomInputSectionStyles = Template.bind({});

WithCustomInputSectionStyles.args = {
  label: "Label Text",
  min: 0,
  max: 1,
  step: 0.1,
  inputSectionStyles: {
    backgroundColor: "lightgreen",
    padding: 3,
  },
  sliderContainerStyles: {
    backgroundColor: "lightgray",
    padding: 2,
  },
  sliderValue: 0.5,
};

export const WithCustomSliderContainerStyles = Template.bind({});

WithCustomSliderContainerStyles.args = {
  label: "Label Text",
  min: 0,
  max: 1,
  step: 0.1,
  inputSectionStyles: {
    backgroundColor: "lightblue",
    padding: 2,
  },
  sliderContainerStyles: {
    backgroundColor: "lightyellow",
    padding: 3,
  },
  sliderValue: 0.5,
};

export const WithMinAndMax = Template.bind({});

WithMinAndMax.args = {
  label: "Label Text",
  min: 10,
  max: 100,
  step: 1,
  sliderValue: 50,
};

export const WithStep = Template.bind({});

WithStep.args = {
  label: "Label Text",
  min: 0,
  max: 1,
  step: 0.01,
  sliderValue: 0.5,
};
