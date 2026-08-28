import React from "react";

import ChartsGenerator from "./ChartsGenerator";
import logger from "src/utils/logger";

const meta = {
  component: ChartsGenerator,
  title: "UI Components/ChartsGenerator",
};

export default meta;

const Template = (args) => (
  <ChartsGenerator
    {...args}
    id="chart-1"
    series={[
      {
        name: "Series 1",
        data: [
          [new Date("2022-01-01").getTime(), 100],
          [new Date("2022-01-02").getTime(), 120],
          [new Date("2022-01-03").getTime(), 150],
          [new Date("2022-01-04").getTime(), 180],
          [new Date("2022-01-05").getTime(), 200],
        ],
      },
      {
        name: "Series 2",
        data: [
          [new Date("2022-01-01").getTime(), 50],
          [new Date("2022-01-02").getTime(), 70],
          [new Date("2022-01-03").getTime(), 90],
          [new Date("2022-01-04").getTime(), 110],
          [new Date("2022-01-05").getTime(), 130],
        ],
      },
    ]}
    label="Chart Label"
    onZoom={(dates) => logger.debug("Zoomed to:", dates)}
  />
);

export const Default = Template.bind({});
Default.args = {};
