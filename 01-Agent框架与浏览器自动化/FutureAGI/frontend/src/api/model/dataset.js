import { useInfiniteQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import axios, { createQueryString, endpoints, fetcher } from "src/utils/axios";
import useSWR from "swr";

export function useGetModelDataset(modelId, options = null) {
  const URL = `${endpoints.dataset.list}/${modelId}/`;

  const params = !options ? {} : options;

  const queryString = createQueryString(params);
  const URLWithParams = queryString ? `${URL}?${queryString}` : URL;

  const { data, isLoading, error, isValidating } = useSWR(
    URLWithParams,
    fetcher,
  );

  const memoizedValue = useMemo(
    () => ({
      datasets: data,
      datasetLoading: isLoading,
      datasetError: error,
      datasetValidating: isValidating,
    }),
    [data, error, isLoading, isValidating],
  );

  return memoizedValue;
}

export function useGetDatasetDetails(modelId, details) {
  const URL = `${endpoints.dataset.summary}/${modelId}/`;
  const params = !details ? {} : details;

  const queryString = createQueryString(params);
  const URLWithParams = queryString ? `${URL}?${queryString}` : URL;

  const { data, isLoading, error, isValidating } = useSWR(
    URLWithParams,
    fetcher,
  );

  const memoizedValue = useMemo(
    () => ({
      datasetDetails: data,
      datasetDetailsLoading: isLoading,
      datasetDetailsError: error,
      datasetDetailsValidating: isValidating,
    }),
    [data, error, isLoading, isValidating],
  );

  return memoizedValue;
}

export async function updateBaselineDataset(modelId, details) {
  const URL = `${endpoints.dataset.list}/${modelId}/`;
  const data = details;
  await axios.post(URL, data);
}

export const useGetPropertyList = (options) => {
  const _qkey = options?.queryKey ?? [];
  const _qParams = options?.params ?? {};
  const _queryParams = useInfiniteQuery({
    ...options,
    queryKey: ["dataset-properties-list", ..._qkey],
    getNextPageParam: (o) => (o.data.next ? o.data.current_page + 1 : null),
    queryFn: ({ pageParam }) =>
      axios.get(`${endpoints.dataset.propertyList}`, {
        params: {
          page: pageParam ? pageParam : 1,
          ..._qParams,
        },
      }),
    initialPageParam: 1,
    staleTime: 30 * 60 * 1000, // 30 min stale time
  });

  const mergedData = useMemo(
    () =>
      _queryParams.data?.pages.reduce(
        (acc, curr) => [...acc, ...curr.data.results],
        [],
      ) || [],
    [_queryParams.data],
  );

  return { mergedData, ..._queryParams };
};
