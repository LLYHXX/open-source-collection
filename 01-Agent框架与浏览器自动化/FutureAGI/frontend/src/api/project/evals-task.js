import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export const useGetProjectById = (projectId, options) => {
  return useQuery({
    queryKey: ["observe-project-by-id", projectId],
    queryFn: () => axios.get(endpoints.project.getProjectById(projectId)),
    select: (d) => d.data,
    staleTime: 1 * 60 * 1000, // 1 min stale time
    ...options,
  });
};
