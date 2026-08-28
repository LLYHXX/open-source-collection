import { useInfiniteQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import axios, { endpoints } from "src/utils/axios";

export const usePromptVersions = (id) => {
  const _queryParams = useInfiniteQuery({
    queryKey: ["prompt-versions", id],
    queryFn: ({ pageParam }) =>
      axios.get(endpoints.develop.runPrompt.getPromptVersions(), {
        params: {
          template_id: id,
          page: pageParam,
        },
      }),
    getNextPageParam: (o) => {
      const nextPage = o.data.next ? o.data.current_page + 1 : null;
      return nextPage;
    },
    initialPageParam: 1,
    enabled: !!id,
  });

  const versions = useMemo(
    () =>
      _queryParams.data?.pages.reduce(
        (acc, curr) => [...acc, ...curr.data.results],
        [],
      ) || [],
    [_queryParams.data],
  );

  return { versions, ..._queryParams };
};
