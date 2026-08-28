import _ from "lodash";
import { useTestRunsGridStoreShallow } from "./states";
import { useMemo } from "react";
import { AGENT_TYPES } from "../agents/constants";

// Re-export shared hook for backwards compatibility
export { useCancelExecution } from "src/sections/common/simulation";

export const ROLE_MAPPER = {
  user: "FAGI Simulator",
  assistant: "Agent",
};

export const formatRole = (
  role,
  agentName,
  simulatorName,
  callType,
  simulationCallType,
) => {
  const lowerRole = _.toLower(role);
  if (simulationCallType === AGENT_TYPES.CHAT) {
    return _.capitalize(role);
  }
  if (role === "assistant" && agentName) {
    return agentName;
  }
  return ROLE_MAPPER[lowerRole] ?? _.capitalize(role);
};

export const useTestRunsSelectedCount = () => {
  // With the MUI DataTable migration, the zustand store is the single source
  // of truth for selection. `selectAll` is always false (no cross-page
  // select-all in the MUI DataTable), so the selected count is simply the
  // length of the `toggledNodes` array.
  const { toggledNodes } = useTestRunsGridStoreShallow((s) => ({
    toggledNodes: s.toggledNodes,
  }));
  return toggledNodes.length;
};

export const useScenarioColumnConfig = (allColumns, apiResponse) => {
  const scenarioColumnConfig = useMemo(() => {
    const data = apiResponse;

    const scenariosDetail =
      data?.scenarios_detail ?? data?.scenariosDetail ?? [];

    const columnConfigs = scenariosDetail.flatMap((detail) => {
      const datasetColumnConfig =
        detail?.dataset_column_config ?? detail?.datasetColumnConfig ?? {};
      return Object.entries(datasetColumnConfig)
        .map((columnConfig) => ({
          field: columnConfig[0],
          headerName:
            columnConfig[1]["name"] &&
            `${columnConfig[1]["name"]} (${detail?.name})`,
          dataType: "text",
        }))
        .filter((item) => item.headerName !== undefined);
    });

    const newColsList = [...allColumns, ...columnConfigs];

    return newColsList;
  }, [apiResponse, allColumns]);

  return scenarioColumnConfig;
};
