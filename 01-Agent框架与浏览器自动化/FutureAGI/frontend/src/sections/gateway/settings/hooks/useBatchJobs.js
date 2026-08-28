import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { enqueueSnackbar } from "notistack";

export function useSubmitBatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ gatewayId, requests, maxConcurrency = 5 }) => {
      const { data } = await axios.post(
        endpoints.gateway.batch.submit(gatewayId),
        { requests, max_concurrency: maxConcurrency },
      );
      return data.result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agentcc-batch-jobs"] });
      enqueueSnackbar("Batch job submitted", { variant: "success" });
    },
    onError: (err) => {
      enqueueSnackbar(
        err?.response?.data?.message || "Failed to submit batch",
        { variant: "error" },
      );
    },
  });
}

export function useBatchStatus(gatewayId, batchId) {
  return useQuery({
    queryKey: ["agentcc-batch-status", gatewayId, batchId],
    queryFn: async () => {
      const { data } = await axios.get(endpoints.gateway.batch.get(gatewayId), {
        params: { batch_id: batchId },
      });
      return data.result;
    },
    enabled: Boolean(gatewayId) && Boolean(batchId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "cancelled") return false;
      return 3000;
    },
    staleTime: 2000,
  });
}

export function useCancelBatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ gatewayId, batchId }) => {
      const { data } = await axios.post(
        endpoints.gateway.batch.cancel(gatewayId),
        { batch_id: batchId },
      );
      return data.result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agentcc-batch-status"] });
      enqueueSnackbar("Batch job cancelled", { variant: "info" });
    },
    onError: (err) => {
      enqueueSnackbar(
        err?.response?.data?.message || "Failed to cancel batch",
        { variant: "error" },
      );
    },
  });
}
