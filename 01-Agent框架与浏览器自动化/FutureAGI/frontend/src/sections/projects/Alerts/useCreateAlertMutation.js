import { useMutation } from "@tanstack/react-query";
import { enqueueSnackbar } from "notistack";
import axios, { endpoints } from "src/utils/axios";
import { Events, PropertyName, trackEvent } from "src/utils/Mixpanel";

export const useCreateAlertMutation = ({
  metricType,
  onSuccessCallback,
  reset,
  handleClose,
}) => {
  return useMutation({
    mutationFn: (data) => axios.post(endpoints.project.createMonitor, data),

    onSuccess: (data, variables) => {
      enqueueSnackbar("Alert created successfully", { variant: "success" });

      trackEvent(Events.createAlertConfirmed, {
        [PropertyName.formFields]: {
          ...variables,
          metricType,
          thresholdType: variables?.threshold_type,
        },
      });

      if (typeof handleClose === "function") handleClose();
      if (typeof reset === "function") reset();

      if (typeof onSuccessCallback === "function") {
        onSuccessCallback(data, variables);
      }
    },
  });
};
