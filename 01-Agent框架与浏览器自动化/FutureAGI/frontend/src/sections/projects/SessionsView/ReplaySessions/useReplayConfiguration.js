import { createContext, useContext } from "react";

/**
 * Configuration context for Replay components
 * Allows different variants (traces, sessions, etc.) to customize:
 * - Copy/text content
 * - API endpoints
 * - Callback handlers
 * - Behavior variations
 */
const ReplayConfigurationContext = createContext(null);

/**
 * Hook to access replay configuration from context
 * Returns null if context is not provided (for graceful fallback)
 * Always call this hook unconditionally at the top level
 */
export const useReplayConfiguration = () => {
  return useContext(ReplayConfigurationContext);
};

export default ReplayConfigurationContext;
