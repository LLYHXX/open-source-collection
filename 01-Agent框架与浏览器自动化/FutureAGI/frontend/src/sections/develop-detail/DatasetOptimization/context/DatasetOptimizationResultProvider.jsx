/**
 * Dataset Optimization Result Provider
 *
 * Re-exports the shared OptimizationResultGridProvider for backward compatibility.
 * New code should import directly from 'src/components/optimization'.
 */

import { OptimizationResultGridProvider } from "src/components/optimization";

// Re-export shared provider with Dataset-specific name for backward compatibility
const DatasetOptimizationResultProvider = OptimizationResultGridProvider;

export default DatasetOptimizationResultProvider;
