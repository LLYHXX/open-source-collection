import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

const EXP_KEY = "agentcc-shadow-experiments";
const RESULT_KEY = "agentcc-shadow-results";

// ── Experiments ──────────────────────────────────────────────

export function useExperiments(params = {}) {
  return useQuery({
    queryKey: [EXP_KEY, params],
    queryFn: async () => {
      const { data } = await axios.get(
        endpoints.gateway.shadowExperiments.list,
        { params },
      );
      return data.result || [];
    },
    staleTime: 30000,
    placeholderData: keepPreviousData,
  });
}

export function useExperimentDetail(id) {
  return useQuery({
    queryKey: [EXP_KEY, "detail", id],
    queryFn: async () => {
      const { data } = await axios.get(
        endpoints.gateway.shadowExperiments.detail(id),
      );
      return data.result;
    },
    enabled: Boolean(id),
    staleTime: 15000,
  });
}

export function useExperimentStats(id) {
  return useQuery({
    queryKey: [EXP_KEY, "stats", id],
    queryFn: async () => {
      const { data } = await axios.get(
        endpoints.gateway.shadowExperiments.stats(id),
      );
      return data.result;
    },
    enabled: Boolean(id),
    staleTime: 30000,
  });
}

export function useCreateExperiment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload) => {
      const { data } = await axios.post(
        endpoints.gateway.shadowExperiments.create,
        payload,
      );
      return data.result;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [EXP_KEY] }),
  });
}

export function useUpdateExperiment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }) => {
      const { data } = await axios.patch(
        endpoints.gateway.shadowExperiments.update(id),
        payload,
      );
      return data.result;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [EXP_KEY] }),
  });
}

export function useDeleteExperiment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      const { data } = await axios.delete(
        endpoints.gateway.shadowExperiments.delete(id),
      );
      return data.result;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [EXP_KEY] }),
  });
}

export function usePauseExperiment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      const { data } = await axios.patch(
        endpoints.gateway.shadowExperiments.pause(id),
      );
      return data.result;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [EXP_KEY] }),
  });
}

export function useResumeExperiment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      const { data } = await axios.patch(
        endpoints.gateway.shadowExperiments.resume(id),
      );
      return data.result;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [EXP_KEY] }),
  });
}

export function useCompleteExperiment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      const { data } = await axios.patch(
        endpoints.gateway.shadowExperiments.complete(id),
      );
      return data.result;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: [EXP_KEY] }),
  });
}

// ── Shadow Results ───────────────────────────────────────────

export function useShadowResults(params = {}) {
  return useQuery({
    queryKey: [RESULT_KEY, params],
    queryFn: async () => {
      const { data } = await axios.get(endpoints.gateway.shadowResults.list, {
        params,
      });
      // paginated response: { results, count, next, previous }
      if (data.result?.results) return data.result;
      return { results: data.result || [], count: 0 };
    },
    enabled: Boolean(params.experiment),
    staleTime: 15000,
    placeholderData: keepPreviousData,
  });
}

export function useShadowResultDetail(id) {
  return useQuery({
    queryKey: [RESULT_KEY, "detail", id],
    queryFn: async () => {
      const { data } = await axios.get(
        endpoints.gateway.shadowResults.detail(id),
      );
      return data.result;
    },
    enabled: Boolean(id),
    staleTime: 15000,
  });
}
