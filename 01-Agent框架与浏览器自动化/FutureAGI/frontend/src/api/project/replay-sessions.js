import { useMutation } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export const useCreateReplaySessions = (options = {}) => {
  return useMutation({
    mutationFn: async (data) => {
      return axios.post(endpoints.project.replaySession, data);
    },
    ...options,
  });
};
