import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { enqueueSnackbar } from "notistack";

export const useDeleteAnnotationLabel = ({ onSuccess } = {}) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) =>
      axios.delete(endpoints.project.deleteLabel(), {
        params: { label_id: id },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["project-annotations-labels"],
      });
      queryClient.invalidateQueries({
        queryKey: ["project-annotations-labels-paginated"],
      });
      queryClient.invalidateQueries({ queryKey: ["project-compare-runs"] });
      queryClient.invalidateQueries({ queryKey: ["span-annotation"] });
      enqueueSnackbar("Label has been deleted", { variant: "success" });
      onSuccess?.();
    },
  });
};
