import React from "react";
import { Card } from "@mui/material";
import PropTypes from "prop-types";
import { useGetDatasetDetails } from "src/api/model/dataset";
import { DatasetFilter } from "src/components/selectors";

import DriftCharts from "./drift-charts";

export default function DatasetDrift({ model }) {
  const { datasetDetails } = useGetDatasetDetails(model.id);

  return (
    <>
      <DatasetFilter datasets={datasetDetails} />
      <Card>
        <DriftCharts />
      </Card>
    </>
  );
}

DatasetDrift.propTypes = {
  model: PropTypes.object,
};
