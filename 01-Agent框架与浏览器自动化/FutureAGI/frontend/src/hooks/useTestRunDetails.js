import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

export const useTestRunDetails = (testId) => {
  const result = useQuery({
    queryKey: ["test-runs-detail", testId],
    queryFn: () => axios.get(endpoints.runTests.detail(testId)),
    select: (d) => d.data,
    enabled: Boolean(testId),
  });

  return {
    data: result.data,
    loading: {
      isPending: result.isLoading,
      isFetching: result.isFetching,
    },
    refetch: result.refetch,
    error: result.error,
    isSuccess: result.isSuccess,
    isError: result.isError,
    raw: result,
  };
};

export default useTestRunDetails;
