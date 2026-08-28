import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

/**
 * Fetch full trace detail — trace + span tree + evals + annotations + summary + graph.
 * Uses the enhanced GET /tracer/trace/{id}/ endpoint (Phase 8).
 */
export const useGetTraceDetail = (traceId) => {
  return useQuery({
    queryKey: ["trace-detail", traceId],
    queryFn: () => axios.get(endpoints.project.getTrace(traceId)),
    select: (d) => d.data?.result,
    enabled: !!traceId,
    staleTime: 30_000,
  });
};
