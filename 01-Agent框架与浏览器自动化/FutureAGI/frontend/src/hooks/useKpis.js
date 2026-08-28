import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export default function useKpis(executionId, options = {}) {
  const queryKey = ["test-execution-detail", "KPIS", executionId];

  const query = useQuery({
    queryKey,
    queryFn: () => axios.get(endpoints.testExecutions.kpis(executionId)),
    enabled: options.enabled ?? !!executionId,
    select: (d) => d.data,
    refetchInterval: options.refetch ? 5000 : false,
    staleTime: 1000 * 60 * 5, // 5 minutes
    ...options,
  });

  return {
    ...query,
    isPending: query.isFetching || query.isLoading,
  };
}
