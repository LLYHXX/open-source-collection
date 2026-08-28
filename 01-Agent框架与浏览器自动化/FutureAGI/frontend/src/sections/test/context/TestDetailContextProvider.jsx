import React, { useCallback, useMemo, useRef } from "react";
import { TestDetailContext } from "./TestDetailContext";
import PropTypes from "prop-types";
import { useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router";
import useTestRunDetails from "src/hooks/useTestRunDetails";

const TestDetailContextProvider = ({ children, executionsCount }) => {
  const testRunsGridApi = useRef(null);
  const queryClient = useQueryClient();
  const { testId } = useParams();

  const { data: testData, loading } = useTestRunDetails(testId);
  const isTestDataPending = loading?.isPending;

  const setTestRunGridApi = useCallback((api) => {
    testRunsGridApi.current = api;
  }, []);

  const getTestRunGridApi = useCallback(() => {
    return testRunsGridApi.current;
  }, []);

  const refreshTestRunGrid = useCallback(() => {
    queryClient.invalidateQueries({
      queryKey: ["test-runs-executions", testId],
    });
    if (testRunsGridApi.current) {
      testRunsGridApi.current.refreshServerSide();
    }
  }, [queryClient, testId]);

  const value = useMemo(
    () => ({
      setTestRunGridApi,
      getTestRunGridApi,
      refreshTestRunGrid,
      testData,
      isTestDataPending,
      executionsCount,
    }),
    [
      getTestRunGridApi,
      setTestRunGridApi,
      refreshTestRunGrid,
      testData,
      isTestDataPending,
      executionsCount,
    ],
  );

  return (
    <TestDetailContext.Provider value={value}>
      {children}
    </TestDetailContext.Provider>
  );
};

TestDetailContextProvider.propTypes = {
  children: PropTypes.any,
  executionsCount: PropTypes.number,
};

export default TestDetailContextProvider;
