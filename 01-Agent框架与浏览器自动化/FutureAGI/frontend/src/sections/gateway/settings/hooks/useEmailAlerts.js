import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

const QUERY_KEY = ["agentcc", "email-alerts"];

export function useEmailAlerts() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      const { data } = await axios.get(endpoints.gateway.emailAlerts.list);
      return data?.result ?? [];
    },
  });
}

export function useCreateEmailAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload) => {
      const { data } = await axios.post(
        endpoints.gateway.emailAlerts.create,
        payload,
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useUpdateEmailAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...payload }) => {
      const { data } = await axios.patch(
        endpoints.gateway.emailAlerts.update(id),
        payload,
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useDeleteEmailAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      const { data } = await axios.delete(
        endpoints.gateway.emailAlerts.delete(id),
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEY }),
  });
}

export function useTestEmailAlert() {
  return useMutation({
    mutationFn: async ({ id, recipientOverride }) => {
      const payload = {};
      if (recipientOverride) {
        payload.recipient_override = recipientOverride;
      }
      const { data } = await axios.post(
        endpoints.gateway.emailAlerts.test(id),
        payload,
      );
      return data;
    },
  });
}
