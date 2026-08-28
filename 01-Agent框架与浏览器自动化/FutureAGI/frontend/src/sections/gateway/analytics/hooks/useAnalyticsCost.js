import { useQuery, keepPreviousData } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export function useAnalyticsCost({
  start,
  end,
  groupBy,
  topN,
  gatewayId,
} = {}) {
  const params = {};
  if (start) params.start = start;
  if (end) params.end = end;
  if (groupBy) params.group_by = groupBy;
  if (topN) params.top_n = topN;
  if (gatewayId) params.gateway_id = gatewayId;

  return useQuery({
    queryKey: ["analytics", "cost", params],
    queryFn: async () => {
      const { data } = await axios.get(endpoints.gateway.analyticsCost, {
        params,
      });
      return data.result;
    },
    placeholderData: keepPreviousData,
    staleTime: 60000,
    refetchOnWindowFocus: false,
  });
}
