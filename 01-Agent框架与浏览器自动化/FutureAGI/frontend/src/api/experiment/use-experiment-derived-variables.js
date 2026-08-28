import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export const useExperimentDerivedVariables = (open, experimentId) => {
  return useQuery({
    queryKey: ["experiment", "derived-variables", experimentId],
    queryFn: () =>
      axios.get(
        endpoints.develop.experiment.getExperimentDerivedVariables(
          experimentId,
        ),
      ),
    enabled: open && !!experimentId,
    select: (d) => d.data?.result,
  });
};
