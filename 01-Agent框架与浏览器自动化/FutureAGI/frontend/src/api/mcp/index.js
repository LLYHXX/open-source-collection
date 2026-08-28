import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { enqueueSnackbar } from "notistack";

// ---------------------------------------------------------------------------
// Query Keys
// ---------------------------------------------------------------------------

export const mcpKeys = {
  all: ["mcp"],
  config: () => [...mcpKeys.all, "config"],
  sessions: () => [...mcpKeys.all, "sessions"],
  tools: () => [...mcpKeys.all, "tools"],
};

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

export const useMCPConfig = (options = {}) => {
  return useQuery({
    queryKey: mcpKeys.config(),
    queryFn: () => axios.get(endpoints.mcp.config),
    select: (d) => {
      const raw = d.data;
      return raw?.result || raw?.data || raw;
    },
    staleTime: 1000 * 60 * 2,
    ...options,
  });
};

export const useMCPSessions = (options = {}) => {
  return useQuery({
    queryKey: mcpKeys.sessions(),
    queryFn: () => axios.get(endpoints.mcp.sessions),
    select: (d) => {
      const raw = d.data;
      const result = raw?.result || raw?.data || raw;
      return result?.sessions || (Array.isArray(result) ? result : []);
    },
    refetchInterval: 30000,
    staleTime: 1000 * 15,
    ...options,
  });
};

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export const useUpdateMCPToolGroups = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => axios.put(endpoints.mcp.toolGroups, data),
    onSuccess: () => {
      enqueueSnackbar("Tool groups updated successfully", {
        variant: "success",
      });
      queryClient.invalidateQueries({
        queryKey: mcpKeys.config(),
      });
    },
    onError: (error) => {
      const msg =
        error?.response?.data?.message ||
        error?.response?.data?.detail ||
        "Failed to update tool groups";
      enqueueSnackbar(msg, { variant: "error" });
    },
  });
};
