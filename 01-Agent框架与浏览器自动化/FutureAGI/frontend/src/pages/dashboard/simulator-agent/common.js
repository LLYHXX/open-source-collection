import SimulatorAgentCellRenderer from "src/components/simulator-agent/SimulatorAgentCellRenderer";
import { PERMISSIONS, RolePermission } from "src/utils/rolePermissionMapping";

export const getSimulatorAgentColumnDefs = (onEdit, onDelete, role) => {
  return [
    {
      field: "name",
      headerName: "Name",
      flex: 2,
      minWidth: 200,
      cellRenderer: SimulatorAgentCellRenderer,
    },
    {
      field: "model",
      headerName: "Model",
      flex: 0.7,
      minWidth: 150,
      cellRenderer: SimulatorAgentCellRenderer,
    },
    {
      field: "voice_provider",
      headerName: "Voice Provider",
      flex: 0.7,
      minWidth: 150,
      cellRenderer: SimulatorAgentCellRenderer,
    },
    {
      field: "voice_name",
      headerName: "Voice Name",
      flex: 0.7,
      minWidth: 150,
      cellRenderer: SimulatorAgentCellRenderer,
    },
    {
      field: "llm_temperature",
      headerName: "Temperature",
      flex: 0.5,
      minWidth: 120,
      cellRenderer: SimulatorAgentCellRenderer,
    },
    {
      field: "created_at",
      headerName: "Created At",
      flex: 0.7,
      minWidth: 150,
      cellRenderer: SimulatorAgentCellRenderer,
    },
    ...(RolePermission.SIMULATION_AGENT[PERMISSIONS.UPDATE][role] &&
    RolePermission.SIMULATION_AGENT[PERMISSIONS.DELETE][role]
      ? [
          {
            field: "actions",
            headerName: "Actions",
            width: 50,
            sortable: false,
            disableColumnMenu: true,
            cellRenderer: SimulatorAgentCellRenderer,
            cellRendererParams: {
              onEdit: onEdit,
              onDelete: onDelete,
            },
          },
        ]
      : []),
  ];
};
