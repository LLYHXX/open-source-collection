import { useMemo } from "react";
import { useProviderHealth } from "../providers/hooks/useGatewayConfig";
import { useGatewayContext } from "../context/useGatewayContext";

/**
 * Returns the list of models actually configured across all providers.
 * Use this instead of hardcoded model lists.
 *
 * @returns {string[]} Sorted, deduplicated list of model names.
 */
export function useAvailableModels() {
  const { gatewayId } = useGatewayContext();
  const { data: healthData } = useProviderHealth(gatewayId);

  return useMemo(() => {
    const providers = healthData?.providers || [];
    const modelSet = new Set();
    const list = Array.isArray(providers)
      ? providers
      : Object.values(providers);
    list.forEach((p) => {
      if (Array.isArray(p?.models)) p.models.forEach((m) => modelSet.add(m));
    });
    return Array.from(modelSet).sort();
  }, [healthData]);
}
