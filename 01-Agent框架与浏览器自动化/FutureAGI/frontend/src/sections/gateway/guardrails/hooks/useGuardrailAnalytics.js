import { useQuery, keepPreviousData } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

const GA_KEY = "agentcc-guardrail-analytics";

export function useGuardrailOverview(params = {}) {
  return useQuery({
    queryKey: [GA_KEY, "overview", params],
    queryFn: async () => {
      const { data } = await axios.get(
        endpoints.gateway.guardrailAnalytics.overview,
        { params },
      );
      return data.result || {};
    },
    staleTime: 60000,
    placeholderData: keepPreviousData,
  });
}

export function useGuardrailRules(params = {}) {
  return useQuery({
    queryKey: [GA_KEY, "rules", params],
    queryFn: async () => {
      const { data } = await axios.get(
        endpoints.gateway.guardrailAnalytics.rules,
        { params },
      );
      const result = data.result || {};
      return Array.isArray(result) ? result : result.rules || [];
    },
    staleTime: 60000,
    placeholderData: keepPreviousData,
  });
}

export function useGuardrailTrends(params = {}) {
  return useQuery({
    queryKey: [GA_KEY, "trends", params],
    queryFn: async () => {
      const { data } = await axios.get(
        endpoints.gateway.guardrailAnalytics.trends,
        { params },
      );
      const result = data.result || {};
      return Array.isArray(result) ? result : result.series || [];
    },
    staleTime: 60000,
    placeholderData: keepPreviousData,
  });
}
