import React from "react";
import { Card, CardHeader, Collapse, Grid, IconButton } from "@mui/material";
import PropTypes from "prop-types";
import { useGetDatasetDetails } from "src/api/model/dataset";
import { DatasetMetricChart } from "src/components/charts";
import Iconify from "src/components/iconify";
import { DatasetFilter } from "src/components/selectors";
import { useBoolean } from "src/hooks/use-boolean";

import DatasetSummary from "./performance/dataset-summary";

export default function ModelOverview({ model }) {
  const collapsible = useBoolean(true);

  const { datasetDetails } = useGetDatasetDetails(model.id);

  const modelSummary = (
    <>
      <Card
        sx={{
          p: 0,
          // minWidth: 300,
          // border: "1px solid rgba(211,211,211,0.6)",
        }}
      >
        <CardHeader
          sx={{
            p: 2,
            // minWidth: 300,
            // border: "1px solid rgba(211,211,211,0.6)",
          }}
          title="Model Overview"
          action={
            <IconButton
              size="small"
              color={collapsible.value ? "inherit" : "default"}
              onClick={collapsible.onToggle}
            >
              <Iconify
                icon={
                  collapsible.value
                    ? "eva:arrow-ios-upward-fill"
                    : "eva:arrow-ios-downward-fill"
                }
              />
            </IconButton>
          }
        />

        <Collapse in={collapsible.value} unmountOnExit>
          <Grid container>
            <Grid item xs={3} />
          </Grid>
        </Collapse>
      </Card>
    </>
  );

  return (
    <>
      {modelSummary}
      <DatasetFilter
        datasets={datasetDetails}
        showComparison={true}
        isBaseline={true}
      />

      <Card>
        <DatasetMetricChart isBrush={false} />
      </Card>

      <Card sx={{ mt: 2 }}>
        <DatasetSummary dataset={{}} model={model} />
      </Card>
    </>
  );
}

ModelOverview.propTypes = {
  model: PropTypes.object,
};
