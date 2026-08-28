import { useMemo } from "react";
import {
  useOrgConfig,
  useCreateOrgConfig,
} from "../../providers/hooks/useOrgConfig";

/**
 * Wraps useOrgConfig to expose just the routing section
 * and a save function that merges routing changes back into the full config.
 */
export function useFallbackConfig() {
  const { data: orgConfig, isLoading, error, refetch } = useOrgConfig();
  const createMutation = useCreateOrgConfig();

  const routing = useMemo(() => orgConfig?.routing || {}, [orgConfig]);

  /**
   * Save routing changes by creating a new org config version.
   * Merges the provided routing object into the existing org config.
   */
  const saveRouting = (newRouting, description) => {
    const payload = {
      providers: orgConfig?.providers || {},
      guardrails: orgConfig?.guardrails || {},
      routing: newRouting,
      cache: orgConfig?.cache || {},
      rate_limiting: orgConfig?.rateLimiting || orgConfig?.rate_limiting || {},
      budgets: orgConfig?.budgets || {},
      cost_tracking: orgConfig?.costTracking || orgConfig?.cost_tracking || {},
      ip_acl: orgConfig?.ipAcl || orgConfig?.ip_acl || {},
      alerting: orgConfig?.alerting || {},
      privacy: orgConfig?.privacy || {},
      tool_policy: orgConfig?.toolPolicy || orgConfig?.tool_policy || {},
      change_description:
        description || "Updated fallback & reliability config",
    };
    return createMutation.mutateAsync(payload);
  };

  return {
    routing,
    orgConfig,
    isLoading,
    error,
    refetch,
    saveRouting,
    isSaving: createMutation.isPending,
  };
}
