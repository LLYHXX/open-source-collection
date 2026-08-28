import { useInfiniteQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export const useGetPromptLabels = () => {
  return useInfiniteQuery({
    queryKey: ["prompt-labels"],
    queryFn: ({ pageParam }) =>
      axios.get(endpoints.develop.runPrompt.promptLabels, {
        params: {
          page: pageParam,
          limit: 10,
        },
      }),
    getNextPageParam: ({ data }) =>
      data?.next ? data?.current_page + 1 : null,
    initialPageParam: 1,
    staleTime: Infinity,
    select: (data) => data.pages.flatMap((page) => page.data.results),
  });
};
