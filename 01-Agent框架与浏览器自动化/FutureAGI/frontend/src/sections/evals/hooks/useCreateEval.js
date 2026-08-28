import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

/**
 * Hook to create a new eval template via the v2 API.
 * Invalidates the eval list cache on success.
 */
export function useCreateEval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload) => {
      const { data } = await axios.post(
        endpoints.develop.eval.createEvalTemplateV2,
        payload,
      );
      return data?.result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evals", "list"] });
    },
  });
}
