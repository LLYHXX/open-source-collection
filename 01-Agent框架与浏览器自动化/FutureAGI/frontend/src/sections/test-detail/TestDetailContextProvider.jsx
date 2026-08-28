import { useCallback, useMemo, useRef } from "react";
import { TestDetailContext } from "./context/TestDetailContext";
import PropTypes from "prop-types";
import { useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router";

const TestDetailContextProvider = ({ children }) => {
  const gridApi = useRef(null);
  const optimizationGridApi = useRef(null);
  const queryClient = useQueryClient();
  const { executionId } = useParams();

  const setGridApi = useCallback((api) => {
    gridApi.current = api;
  }, []);

  const refreshGrid = useCallback(() => {
    if (gridApi.current) {
      queryClient.invalidateQueries({
        queryKey: ["test-execution-detail-list", executionId],
      });
      gridApi.current.refreshServerSide();
    }
  }, [queryClient, executionId]);

  const getGridApi = useCallback(() => {
    return gridApi.current;
  }, []);

  const setOptimizationGridApi = useCallback((api) => {
    optimizationGridApi.current = api;
  }, []);

  const refreshOptimizationGrid = useCallback(() => {
    if (optimizationGridApi.current) {
      queryClient.invalidateQueries({
        queryKey: ["agent-optimization-runs", executionId],
      });
      optimizationGridApi.current.refreshServerSide();
    }
  }, [queryClient, executionId]);

  const getOptimizationGridApi = useCallback(() => {
    return optimizationGridApi.current;
  }, []);

  const value = useMemo(
    () => ({
      refreshGrid,
      setGridApi,
      getGridApi,
      refreshOptimizationGrid,
      setOptimizationGridApi,
      getOptimizationGridApi,
    }),
    [
      refreshGrid,
      setGridApi,
      getGridApi,
      refreshOptimizationGrid,
      setOptimizationGridApi,
      getOptimizationGridApi,
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
};

export default TestDetailContextProvider;
