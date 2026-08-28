/**
 * Simulation Optimization Result Context
 *
 * Re-exports the shared OptimizationResultGridContext for backward compatibility.
 * New code should import directly from 'src/components/optimization'.
 */

import {
  OptimizationResultGridContext,
  useOptimizationResultGrid,
} from "src/components/optimization";

// Re-export with Simulation-specific names for backward compatibility
export const OptimizationResultContext = OptimizationResultGridContext;
export const useOptimizationResultContext = useOptimizationResultGrid;
