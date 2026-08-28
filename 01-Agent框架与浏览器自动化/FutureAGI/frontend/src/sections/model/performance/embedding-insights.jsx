import React from "react";
import PropTypes from "prop-types";
import { useGetDatasetDetails } from "src/api/model/dataset";
import { DatasetMetricChart } from "src/components/charts";
import { DatasetFilter } from "src/components/selectors";

import EmbeddingExplorer from "../embedding-explorer";

export default function EmbeddingInsights({ model }) {
  const { datasetDetails } = useGetDatasetDetails(model.id);

  return (
    <>
      <DatasetFilter
        datasets={datasetDetails}
        showComparison={true}
        isBaseline={true}
      />

      <DatasetMetricChart isBrush={false} />

      <EmbeddingExplorer />
    </>
  );
}

EmbeddingInsights.propTypes = {
  model: PropTypes.object,
};
