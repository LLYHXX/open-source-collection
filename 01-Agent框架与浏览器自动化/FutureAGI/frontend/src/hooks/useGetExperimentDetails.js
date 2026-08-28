import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export const useGetExperimentDetails = (experimentId) => {
  return useQuery({
    queryKey: ["experiment", experimentId],
    queryFn: async () => {
      return await axios.get(
        endpoints.develop.experiment.getExperimentDetails(experimentId),
      );
    },
    enabled: Boolean(experimentId),
    select: (d) => d?.data?.result,
  });
};
