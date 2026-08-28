/**
 * Shared Optimization Components
 *
 * This module provides reusable components and utilities for optimization result views.
 * Used by both Dataset Optimization and Simulation (Agent Prompt) Optimization.
 *
 * Components:
 * - OptimizationResultGridProvider: Context provider for AG Grid API state
 * - useOptimizationResultGrid: Hook to access grid API
 *
 * @example
 * import {
 *   OptimizationResultGridProvider,
 *   useOptimizationResultGrid,
 * } from 'src/components/optimization';
 */

// Context and Provider for AG Grid API management
export {
  OptimizationResultGridContext,
  useOptimizationResultGrid,
} from "./OptimizationResultGridContext";
export { default as OptimizationResultGridProvider } from "./OptimizationResultGridProvider";
