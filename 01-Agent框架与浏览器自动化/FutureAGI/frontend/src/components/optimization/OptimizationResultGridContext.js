/**
 * Optimization Result Grid Context
 *
 * Shared context for managing AG Grid API state in optimization result views.
 * Used by both Dataset Optimization and Simulation Optimization components.
 *
 * This context provides:
 * - gridApi: Reference to the AG Grid API instance
 * - setGridApi: Function to set the grid API (called from onGridReady)
 * - getGridApi: Function to get the current grid API
 *
 * Usage:
 * 1. Wrap your optimization result components with OptimizationResultGridProvider
 * 2. Use useOptimizationResultGrid() hook to access the grid API
 *
 * @example
 * // In parent component
 * import { OptimizationResultGridProvider } from 'src/components/optimization';
 *
 * <OptimizationResultGridProvider>
 *   <OptimizationResultGrid />
 *   <OptimizationResultBar />
 * </OptimizationResultGridProvider>
 *
 * @example
 * // In child component
 * import { useOptimizationResultGrid } from 'src/components/optimization';
 *
 * const { setGridApi, getGridApi } = useOptimizationResultGrid();
 */

import { createContext, useContext } from "react";

export const OptimizationResultGridContext = createContext({
  gridApi: null,
  setGridApi: () => {},
  getGridApi: () => {},
});

/**
 * Hook to access the optimization result grid context.
 *
 * @returns {{ setGridApi: Function, getGridApi: Function }}
 */
export const useOptimizationResultGrid = () => {
  return useContext(OptimizationResultGridContext);
};
