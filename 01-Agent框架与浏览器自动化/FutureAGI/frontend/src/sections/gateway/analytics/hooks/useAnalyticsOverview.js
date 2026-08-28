import { useQuery, keepPreviousData } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export function useAnalyticsOverview(
  { start, end, gatewayId, apiKeyId } = {},
  options = {},
) {
  const params = {};
  if (start) params.start = start;
  if (end) params.end = end;
  if (gatewayId) params.gateway_id = gatewayId;
  if (apiKeyId) params.api_key_id = apiKeyId;

  return useQuery({
    queryKey: ["analytics", "overview", params],
    queryFn: async () => {
      const { data } = await axios.get(endpoints.gateway.analyticsOverview, {
        params,
      });
      return data.result;
    },
    placeholderData: keepPreviousData,
    staleTime: 60000,
    refetchOnWindowFocus: false,
    ...options,
  });
}
