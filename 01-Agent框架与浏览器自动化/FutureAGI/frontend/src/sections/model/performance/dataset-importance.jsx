import React from "react";
import PropTypes from "prop-types";
import { useGetDatasetDetails } from "src/api/model/dataset";
import BarChart from "src/components/charts/bar-chart";
import { DatasetFilter } from "src/components/selectors";

export default function DatasetImportance({ model }) {
  const { datasetDetails } = useGetDatasetDetails(model.id);

  return (
    <>
      <DatasetFilter
        datasets={datasetDetails}
        showComparison={true}
        isBaseline={true}
      />

      <BarChart size="large" />
    </>
  );
}

DatasetImportance.propTypes = {
  model: PropTypes.object,
};
