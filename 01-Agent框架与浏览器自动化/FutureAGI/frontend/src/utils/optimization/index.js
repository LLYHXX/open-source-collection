/**
 * Shared optimization utilities.
 *
 * This module provides common functions used by both:
 * - Dataset optimization (develop-detail)
 * - Simulation optimization (test-detail/FixMyAgentDrawer)
 */

export {
  getCategories,
  getGraphTooltipComponent,
  getBaseChartOptions,
  updateCrosshairColor,
} from "./graphUtils";

export {
  transformColDefToColumnStructure,
  getOptimizationResultColumnConfig,
  defaultOptimizationColDef,
} from "./columnUtils";
