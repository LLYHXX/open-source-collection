import { useQuery, keepPreviousData } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export function useAnalyticsModels({ start, end, models, gatewayId } = {}) {
  const params = {};
  if (start) params.start = start;
  if (end) params.end = end;
  if (models) params.models = models;
  if (gatewayId) params.gateway_id = gatewayId;

  return useQuery({
    queryKey: ["analytics", "models", params],
    queryFn: async () => {
      const { data } = await axios.get(endpoints.gateway.analyticsModels, {
        params,
      });
      return data.result;
    },
    placeholderData: keepPreviousData,
    staleTime: 60000,
    refetchOnWindowFocus: false,
  });
}
