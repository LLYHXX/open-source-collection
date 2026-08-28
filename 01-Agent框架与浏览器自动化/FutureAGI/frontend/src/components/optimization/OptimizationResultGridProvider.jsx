/**
 * Optimization Result Grid Provider
 *
 * Provides AG Grid API state management for optimization result components.
 * Used by both Dataset Optimization and Simulation Optimization.
 *
 * This provider manages a ref to the AG Grid API, allowing child components
 * to access and manipulate the grid (e.g., for column visibility changes).
 *
 * @example
 * import { OptimizationResultGridProvider } from 'src/components/optimization';
 *
 * const OptimizationResults = () => (
 *   <OptimizationResultGridProvider>
 *     <OptimizationResultBar optimizationData={data} />
 *     <OptimizationResultGrid optimizationId={id} />
 *     <OptimizationResultGraph optimizationId={id} />
 *   </OptimizationResultGridProvider>
 * );
 */

import React, { useRef } from "react";
import { OptimizationResultGridContext } from "./OptimizationResultGridContext";
import PropTypes from "prop-types";

const OptimizationResultGridProvider = ({ children }) => {
  const gridApi = useRef(null);

  const setGridApi = (api) => {
    gridApi.current = api;
  };

  const getGridApi = () => {
    return gridApi.current;
  };

  return (
    <OptimizationResultGridContext.Provider value={{ setGridApi, getGridApi }}>
      {children}
    </OptimizationResultGridContext.Provider>
  );
};

OptimizationResultGridProvider.propTypes = {
  children: PropTypes.node,
};

export default OptimizationResultGridProvider;
