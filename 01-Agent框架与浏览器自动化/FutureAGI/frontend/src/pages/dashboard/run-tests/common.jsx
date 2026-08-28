import React from "react";
import { Typography } from "@mui/material";
import RunTestsActionRenderer from "./CellRenderers/RunTestsActionRenderer";
import RunTestsNameRenderer from "./CellRenderers/RunTestsNameRenderer";
import { formatDistanceToNow } from "date-fns";
import { PERMISSIONS, RolePermission } from "src/utils/rolePermissionMapping";

export const getColumnConfig = (viewDetails, onDelete, role) => {
  return [
    {
      field: "testDetail",
      headerName: "Name",
      flex: 2,
      cellRenderer: RunTestsNameRenderer,
    },
    {
      field: "lastRunAt",
      headerName: "Last Run",
      maxWidth: 200,
      cellRenderer: (params) => (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            px: 1,
            alignContent: "center",
            height: "100%",
          }}
        >
          {params.value
            ? formatDistanceToNow(new Date(params.value), { addSuffix: true })
            : "-"}
        </Typography>
      ),
    },
    ...(RolePermission.SIMULATION_AGENT[PERMISSIONS.UPDATE][role] &&
    RolePermission.SIMULATION_AGENT[PERMISSIONS.DELETE][role]
      ? [
          {
            field: "actions",
            headerName: "Actions",
            cellRenderer: RunTestsActionRenderer,
            maxWidth: 150,
            cellRendererParams: {
              viewDetails: viewDetails,
              onDelete: onDelete,
            },
          },
        ]
      : []),
  ];
};
