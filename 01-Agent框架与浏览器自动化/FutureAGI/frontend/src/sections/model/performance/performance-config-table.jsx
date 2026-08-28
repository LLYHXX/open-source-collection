import { yupResolver } from "@hookform/resolvers/yup";
import { LoadingButton } from "@mui/lab";
import { MenuItem, Stack } from "@mui/material";
import PropTypes from "prop-types";
import React, { useMemo } from "react";
import { useForm } from "react-hook-form";
import { updateModelPerformanceMetric } from "src/api/model/info";
import FormProvider, { RHFSelect } from "src/components/hook-form";
import { useSnackbar } from "src/components/snackbar";
import logger from "src/utils/logger";
import * as Yup from "yup";

export default function PerformanceConfigTable({ datasetDetails, model }) {
  const { enqueueSnackbar } = useSnackbar();

  const NewUserSchema = Yup.object().shape({
    metric: Yup.string().required("Metric is required"),
    positiveClass: Yup.string().required("Positive Class is required"),
  });

  const defaultValues = useMemo(
    () => ({
      metric: model.modelPerformanceMetrics || "",
      positiveClass: model.modelPerformancePositiveClass || "",
    }),
    [datasetDetails, model],
  );

  const methods = useForm({
    resolver: yupResolver(NewUserSchema),
    defaultValues,
  });

  const {
    handleSubmit,
    formState: { isSubmitting },
  } = methods;

  const onSubmit = handleSubmit(async (data) => {
    try {
      await updateModelPerformanceMetric(model.id, data);
      enqueueSnackbar("Update success!");
    } catch (error) {
      logger.error("Failed to update model performance metric", error);
    }
  });

  return (
    <>
      <FormProvider methods={methods} onSubmit={onSubmit}>
        <Stack spacing={2} direction={"column"}>
          {datasetDetails?.performanceMetrics ? (
            <RHFSelect name="metric" label="Metric" size="small">
              {datasetDetails?.performanceMetrics?.map((row) => (
                <MenuItem key={row.value} value={row.value}>
                  {row.name}
                </MenuItem>
              ))}
            </RHFSelect>
          ) : null}
          {datasetDetails?.performanceMetrics ? (
            <RHFSelect name="positiveClass" label="Class" size="small">
              {datasetDetails?.classes?.map((row) => (
                <MenuItem key={row} value={row}>
                  {row}
                </MenuItem>
              ))}
            </RHFSelect>
          ) : null}
        </Stack>
        <Stack alignItems="flex-end" sx={{ mt: 3 }}>
          <LoadingButton
            type="submit"
            variant="contained"
            loading={isSubmitting}
          >
            Save
          </LoadingButton>
        </Stack>
      </FormProvider>
    </>
  );
}

PerformanceConfigTable.propTypes = {
  datasetDetails: PropTypes.object,
  model: PropTypes.object,
};
