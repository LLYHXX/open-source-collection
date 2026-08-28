import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export function useEvalFeedbackList(
  templateId,
  { page = 0, pageSize = 25 } = {},
) {
  return useQuery({
    queryKey: ["evals", "feedback-list", templateId, page, pageSize],
    queryFn: async () => {
      const { data } = await axios.get(
        endpoints.develop.eval.getEvalFeedbackList(templateId),
        { params: { page, page_size: pageSize } },
      );
      return data?.result;
    },
    enabled: !!templateId,
    keepPreviousData: true,
  });
}
