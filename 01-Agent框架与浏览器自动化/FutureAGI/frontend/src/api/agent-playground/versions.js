import {
  useMutation,
  useInfiniteQuery,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

/**
 * Hook for fetching a specific version's detail (nodes, edges, config).
 * @param {string} graphId
 * @param {string} versionId
 * @param {object} options - Additional react-query options
 */
export const useGetVersionDetail = (
  graphId,
  versionId,
  { enabled, ...restOptions } = {},
) =>
  useQuery({
    queryKey: ["agent-playground", "version-detail", graphId, versionId],
    queryFn: () =>
      axios.get(endpoints.agentPlayground.versionDetail(graphId, versionId)),
    select: (res) => res.data?.result,
    staleTime: 0,
    enabled: !!graphId && !!versionId && (enabled ?? true),
    ...restOptions,
  });

/**
 * Hook for saving a draft version (nodes, edges, config) via PUT.
 * @param {object} options - useMutation options
 */
export const useSaveDraftVersion = (options = {}) =>
  useMutation({
    mutationFn: ({ graphId, versionId, payload }) =>
      axios.put(
        endpoints.agentPlayground.versionDetail(graphId, versionId),
        payload,
      ),
    meta: { errorHandled: true },
    onSuccess: (...args) => options.onSuccess?.(...args),
    ...options,
  });

/**
 * Hook for deleting a version via DELETE.
 * Invalidates the versions list cache on success.
 * @param {object} options - useMutation options
 */
export const useDeleteVersion = (options = {}) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ graphId, versionId }) =>
      axios.delete(endpoints.agentPlayground.versionDetail(graphId, versionId)),
    onSuccess: (res, variables, context) => {
      queryClient.invalidateQueries({
        queryKey: ["agent-playground", "graph-versions", variables.graphId],
      });
      options.onSuccess?.(res, variables, context);
    },
    ...options,
  });
};

/**
 * Hook for creating a new draft version via POST.
 * Used when the current version is active and user makes edits.
 * @param {object} options - useMutation options
 */
export const useCreateVersion = (options = {}) =>
  useMutation({
    mutationFn: ({ graphId, payload }) =>
      axios.post(endpoints.agentPlayground.graphVersions(graphId), payload),
    meta: { errorHandled: true },
    ...options,
  });

/**
 * Hook for activating an inactive version (atomic swap with current active).
 * POST /agent-playground/graphs/:id/versions/:version_id/activate/
 * @param {object} options - useMutation options
 */
export const useActivateVersion = (options = {}) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ graphId, versionId }) =>
      axios.post(endpoints.agentPlayground.activateVersion(graphId, versionId)),
    onSuccess: (res, variables, context) => {
      queryClient.invalidateQueries({
        queryKey: ["agent-playground", "graph", variables.graphId],
      });
      queryClient.invalidateQueries({
        queryKey: ["agent-playground", "graph-versions", variables.graphId],
      });
      queryClient.invalidateQueries({
        queryKey: ["agent-playground", "version-detail", variables.graphId],
      });
      options.onSuccess?.(res, variables, context);
    },
    ...options,
  });
};

/**
 * Hook for fetching graph versions with infinite scroll support.
 * Returns all versions ordered newest first. Pagination-ready via getNextPageParam.
 * @param {string} graphId
 * @param {object} options - Additional react-query options
 */
export const useGetGraphVersions = (graphId, options = {}) =>
  useInfiniteQuery({
    queryKey: ["agent-playground", "graph-versions", graphId],
    queryFn: ({ pageParam }) =>
      axios.get(endpoints.agentPlayground.graphVersions(graphId), {
        params: { page_number: pageParam, page_size: 20 },
      }),
    getNextPageParam: (lastPage) =>
      lastPage.data?.result?.metadata?.next_page ?? undefined,
    initialPageParam: 1,
    staleTime: 30 * 1000,
    enabled: !!graphId,
    ...options,
  });
