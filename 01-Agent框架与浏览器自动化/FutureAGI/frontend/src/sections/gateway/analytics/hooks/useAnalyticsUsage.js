import { useQuery, keepPreviousData } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export function useAnalyticsUsage(
  { start, end, granularity, groupBy, gatewayId, apiKeyId } = {},
  options = {},
) {
  const params = {};
  if (start) params.start = start;
  if (end) params.end = end;
  if (granularity) params.granularity = granularity;
  if (groupBy) params.group_by = groupBy;
  if (gatewayId) params.gateway_id = gatewayId;
  if (apiKeyId) params.api_key_id = apiKeyId;

  return useQuery({
    queryKey: ["analytics", "usage", params],
    queryFn: async () => {
      const { data } = await axios.get(endpoints.gateway.analyticsUsage, {
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
