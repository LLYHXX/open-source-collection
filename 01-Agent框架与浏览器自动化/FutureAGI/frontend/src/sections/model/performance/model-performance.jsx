import React, { useState } from "react";
import { Box, Card, ToggleButton, ToggleButtonGroup } from "@mui/material";
import PropTypes from "prop-types";
import { DatasetMetricChart } from "src/components/charts";
import { DatasetFilter } from "src/components/selectors";
import { useGetDatasetDetails } from "src/api/model/dataset";

import EmbeddingExplorer from "../embedding-explorer";
import DataSlices from "../data-slices";
import ModelPredictions from "../model-predictions";

export default function ModelPerformance({ model }) {
  const [currentTab, setCurrentTab] = useState("predictions");
  const { datasetDetails } = useGetDatasetDetails(model.id);

  const currentDate = new Date();
  currentDate.setHours(0, 0, 0, 0);

  const handleTabChange = (event, newAlignment) => {
    setCurrentTab(newAlignment);
  };

  return (
    <>
      <DatasetFilter datasets={datasetDetails} />
      <Card>
        <DatasetMetricChart />
      </Card>

      <Card sx={{ my: 2, mx: 2 }}>
        <ToggleButtonGroup
          value={currentTab}
          exclusive
          onChange={handleTabChange}
          sx={{
            width: "100%",
          }}
        >
          <ToggleButton style={{ flexGrow: 1 }} value="predictions">
            Predictions
          </ToggleButton>
          <ToggleButton style={{ flexGrow: 1 }} value="embeddings">
            Embeddings Viz
          </ToggleButton>
          <ToggleButton style={{ flexGrow: 1 }} value="data-slice">
            Data Slices
          </ToggleButton>
          <ToggleButton style={{ flexGrow: 1 }} value="more">
            More Charts
          </ToggleButton>
        </ToggleButtonGroup>
      </Card>
      {currentTab === "predictions" && <ModelPredictions />}
      {currentTab === "embeddings" && <EmbeddingExplorer />}
      {currentTab === "data-slice" && <DataSlices />}
      {/* {currentTab === "more" && <EmbeddingExplorer></EmbeddingExplorer> } */}

      <Card>
        <Box sx={{ my: 2, mx: 2 }} />
      </Card>
    </>
  );
}

ModelPerformance.propTypes = {
  model: PropTypes.object,
};
