import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export function useCreateCompositeEval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload) => {
      const { data } = await axios.post(
        endpoints.develop.eval.createCompositeEval,
        payload,
      );
      return data?.result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evals", "list"] });
    },
  });
}

export function useCompositeDetail(compositeId, enabled = true) {
  return useQuery({
    queryKey: ["evals", "composite", compositeId],
    queryFn: async () => {
      const { data } = await axios.get(
        endpoints.develop.eval.getCompositeDetail(compositeId),
      );
      return data?.result;
    },
    enabled: Boolean(compositeId) && enabled,
  });
}

export function useExecuteCompositeEval() {
  return useMutation({
    mutationFn: async ({ templateId, payload }) => {
      const { data } = await axios.post(
        endpoints.develop.eval.executeCompositeEval(templateId),
        payload,
      );
      return data?.result;
    },
  });
}

export function useExecuteCompositeEvalAdhoc() {
  return useMutation({
    mutationFn: async (payload) => {
      const { data } = await axios.post(
        endpoints.develop.eval.executeCompositeEvalAdhoc,
        payload,
      );
      return data?.result;
    },
  });
}

export function useUpdateCompositeEval(templateId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload) => {
      const { data } = await axios.patch(
        endpoints.develop.eval.getCompositeDetail(templateId),
        payload,
      );
      return data?.result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["evals", "composite", templateId],
      });
      queryClient.invalidateQueries({
        queryKey: ["evals", "detail", templateId],
      });
      queryClient.invalidateQueries({
        queryKey: ["evals", "versions", templateId],
      });
      queryClient.invalidateQueries({ queryKey: ["evals", "list"] });
    },
  });
}
