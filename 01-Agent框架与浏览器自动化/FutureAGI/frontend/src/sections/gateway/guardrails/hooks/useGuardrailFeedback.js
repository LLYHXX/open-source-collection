import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

const GF_KEY = "agentcc-guardrail-feedback";

export function useGuardrailFeedback(params = {}) {
  return useQuery({
    queryKey: [GF_KEY, params],
    queryFn: async () => {
      const { data } = await axios.get(
        endpoints.gateway.guardrailFeedback.list,
        { params },
      );
      return data.result || [];
    },
    staleTime: 30000,
    placeholderData: keepPreviousData,
  });
}

export function useGuardrailFeedbackSummary(params = {}) {
  return useQuery({
    queryKey: [GF_KEY, "summary", params],
    queryFn: async () => {
      const { data } = await axios.get(
        endpoints.gateway.guardrailFeedback.summary,
        { params },
      );
      return data.result || [];
    },
    staleTime: 60000,
  });
}

export function useCreateGuardrailFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload) => {
      const { data } = await axios.post(
        endpoints.gateway.guardrailFeedback.create,
        payload,
      );
      return data.result;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [GF_KEY] }),
  });
}
