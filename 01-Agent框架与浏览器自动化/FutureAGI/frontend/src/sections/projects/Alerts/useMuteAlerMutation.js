import { useMutation } from "@tanstack/react-query";
import { enqueueSnackbar } from "notistack";
import axios, { endpoints } from "src/utils/axios";

export const useMuteAlertsMutation = ({ onSuccessCallback }) => {
  return useMutation({
    mutationFn: (data) => axios.post(endpoints.project.muteAlerts, data),

    onSuccess: (data, variables) => {
      enqueueSnackbar(data?.data?.result || "Alerts muted successfully", {
        variant: "success",
      });

      if (typeof onSuccessCallback === "function") {
        onSuccessCallback(data, variables);
      }
    },
  });
};
