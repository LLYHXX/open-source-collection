import useSWR from "swr";
import { useMemo } from "react";

import { fetcher, endpoints } from "src/utils/axios";

export function useOverviewData() {
  const URL = endpoints.overview.dashboardSummary;

  const { data, isLoading, error, isValidating } = useSWR(URL, fetcher);

  const memoizedValue = useMemo(
    () => ({
      data: data || [],
      dataLoading: isLoading,
      dataError: error,
      dataValidating: isValidating,
      dataEmpty: !isLoading && !data,
    }),
    [data, error, isLoading, isValidating],
  );

  return memoizedValue;
}
