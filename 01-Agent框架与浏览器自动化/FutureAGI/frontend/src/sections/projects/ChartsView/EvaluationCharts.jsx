import React from "react";
import { Grid, Skeleton, Stack, Typography, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
const LazyChartWrapper = React.lazy(() => import("./LazyChartWrapper"));

export default function EvaluationCharts({ observeId }) {
  const theme = useTheme();
  const { data: expandedEvaluations, isLoading } = useQuery({
    queryKey: ["observe-evaluations", observeId],
    queryFn: () =>
      axios.get(endpoints.project.getTraceEvals(), {
        params: {
          project_id: observeId,
        },
      }),
    select: (res) => res?.data,
    enabled: !!observeId,
  });

  if (
    !Array.isArray(expandedEvaluations?.result) ||
    expandedEvaluations?.result?.length === 0
  ) {
    return null;
  }

  return (
    <Stack flexDirection={"column"} gap={2}>
      {isLoading ? (
        <Skeleton
          variant="text"
          width={150}
          height={60}
          sx={{ marginBottom: theme.spacing(2) }}
        />
      ) : (
        <Typography
          variant="body1"
          fontWeight={"fontWeightSemiBold"}
          gutterBottom
          sx={{
            color: theme.palette.text.primary,
          }}
        >
          Evaluation Metrics
        </Typography>
      )}

      {isLoading ? (
        <Grid container spacing={2}>
          {Array(3).map((_, index) => (
            <Grid key={index} item xs={12} sm={4}>
              <Skeleton variant="rectangular" width="100%" height={250} />
            </Grid>
          ))}
        </Grid>
      ) : (
        <Grid container spacing={2}>
          {expandedEvaluations?.result?.map((evaluation) => (
            <Grid
              key={`${evaluation.id}-${evaluation?.name}`}
              item
              xs={12}
              md={4}
              style={{
                cursor: "pointer",
                transition: "none",
              }}
            >
              <LazyChartWrapper evaluation={evaluation} observeId={observeId} />
            </Grid>
          ))}
        </Grid>
      )}
    </Stack>
  );
}

EvaluationCharts.propTypes = {
  observeId: PropTypes.string,
};
