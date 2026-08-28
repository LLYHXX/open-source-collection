import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export const useGetOptimization = (modelId, optimizeId, options) => {
  return useQuery({
    ...options,
    queryFn: () =>
      axios.get(
        endpoints.optimization.getOptimizationDetail(modelId, optimizeId),
      ),
    queryKey: ["optimization-by-id", modelId, optimizeId],
    select: (d) => d.data?.data,
    staleTime: 1 * 60 * 1000, // 1 min stale time
  });
};
