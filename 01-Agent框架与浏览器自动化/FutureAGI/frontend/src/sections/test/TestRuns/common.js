import { format } from "date-fns";
import TestStatusCellRenderer from "./CellRenderers/TestStatusCellRenderer";
import { formatDuration } from "src/utils/format-time";
import { AGENT_TYPES } from "src/sections/agents/constants";
import { SIMULATION_TYPE } from "src/components/run-tests/common";

export const getTestRunsColDef = (agentType = "voice", simulationType) => {
  // Prompt simulations have their own column config
  if (simulationType === SIMULATION_TYPE.PROMPT) {
    return [
      {
        headerName: "Scenario",
        field: "scenarios",
        flex: 1,
        minWidth: 150,
      },
      {
        headerName: "Run Start Time",
        field: "startTime",
        flex: 1,
        minWidth: 150,
        valueFormatter: (params) => {
          if (!params.value) return "-";
          return format(new Date(params.value), "yyyy-MM-dd HH:mm");
        },
      },
      {
        headerName: "Prompt Version",
        field: "agentVersion",
        flex: 1,
        valueFormatter: (params) => {
          // Backend returns agentVersion with 'v' prefix for prompt simulations
          return params.value || "-";
        },
      },
      {
        headerName: "Total Runs",
        flex: 1,
        minWidth: 100,
        field: "totalChats",
        valueFormatter: (params) => params.value ?? 0,
      },
      {
        headerName: "% Completed",
        flex: 1,
        minWidth: 110,
        field: "successRate",
        valueFormatter: (params) => {
          if (params.value == null) return "-";
          return `${params.value}%`;
        },
      },
      {
        headerName: "Run Status",
        field: "status",
        flex: 1,
        minWidth: 180,
        cellRenderer: TestStatusCellRenderer,
      },
      {
        headerName: "Duration",
        field: "duration",
        flex: 1,
        minWidth: 100,
        valueFormatter: (params) => {
          if (!params.value) return "-";
          return formatDuration(params.value);
        },
      },
    ];
  }

  if (agentType === AGENT_TYPES.CHAT) {
    return [
      {
        headerName: "Scenario",
        field: "scenarios",
        flex: 1,
        minWidth: 150,
      },
      {
        headerName: "Run Start Time",
        field: "startTime",
        flex: 1,
        minWidth: 150,
        valueFormatter: (params) => {
          if (!params.value) return "-";
          return format(new Date(params.value), "yyyy-MM-dd HH:mm");
        },
      },
      {
        headerName: "Total Chats",
        flex: 1,
        minWidth: 100,
        field: "totalChats",
        valueFormatter: (params) => params.value ?? 0,
      },

      {
        headerName: "Run Status",
        field: "status",
        flex: 1,
        minWidth: 180,
        cellRenderer: TestStatusCellRenderer,
      },
      {
        headerName: "Total Turns",
        field: "totalNumberOfFagiAgentTurns",
        flex: 1,
        minWidth: 100,
        valueFormatter: (params) => {
          if (!params.value) return "-";
          return params?.value;
        },
      },
      {
        headerName: "% Chats Completed",
        flex: 1,
        minWidth: 110,
        field: "successRate",
        valueFormatter: (params) => {
          if (params.value == null) return "-";
          return `${params.value}%`;
        },
      },
    ];
  }

  // VOICE agent type
  return [
    {
      headerName: "Scenario",
      field: "scenarios",
      flex: 1,
      minWidth: 150,
    },
    {
      headerName: "Run Start Time",
      field: "startTime",
      flex: 1,
      minWidth: 150,
      valueFormatter: (params) => {
        if (!params.value) return "-";
        return format(new Date(params.value), "yyyy-MM-dd HH:mm");
      },
    },
    {
      headerName: "Agent Definition",
      field: "agent_definition",
      flex: 1,
      valueFormatter: (params) => {
        const { agentDefinition, agentVersion } = params?.data || {};
        return agentDefinition && agentVersion
          ? `${agentDefinition} (${agentVersion})`
          : "-";
      },
    },
    {
      headerName: "Calls Attempted",
      flex: 1,
      minWidth: 100,
      field: "callsAttempted",
    },
    {
      headerName: "% Calls Connected",
      flex: 1,
      minWidth: 110,
      field: "callsConnectedPercentage",
      valueFormatter: (params) => {
        if (params.value == null) return "-";
        return `${params.value}%`;
      },
    },
    {
      headerName: "Run Status",
      field: "status",
      flex: 1,
      minWidth: 180,
      cellRenderer: TestStatusCellRenderer,
    },
    {
      headerName: "Duration",
      field: "duration",
      flex: 1,
      minWidth: 100,
      valueFormatter: (params) => {
        if (!params.value) return "-";
        return formatDuration(params.value);
      },
    },
  ];
};

export const ComponentApiMapping = {
  ToolEvaluationApiKey: "API_KEY_AND_ASSISTANT_ID_REQUIRED",
};
