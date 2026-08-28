import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export const useGetExperimentJSONSchema = (open, experimentId) => {
  return useQuery({
    queryKey: ["experiment", "json-schema", experimentId],
    queryFn: () =>
      axios.get(
        endpoints.develop.experiment.getExperimentJSONSchema(experimentId),
      ),
    enabled: open && !!experimentId,
    select: (d) => d.data?.result,
  });
};
