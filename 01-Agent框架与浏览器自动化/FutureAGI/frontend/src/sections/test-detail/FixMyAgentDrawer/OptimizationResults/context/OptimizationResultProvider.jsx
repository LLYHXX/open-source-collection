/**
 * Simulation Optimization Result Provider
 *
 * Re-exports the shared OptimizationResultGridProvider for backward compatibility.
 * New code should import directly from 'src/components/optimization'.
 */

import { OptimizationResultGridProvider } from "src/components/optimization";

// Re-export shared provider with Simulation-specific name for backward compatibility
const OptimizationResultProvider = OptimizationResultGridProvider;

export default OptimizationResultProvider;
