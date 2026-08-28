import React from "react";
import PropTypes from "prop-types";
import { TableCell, TableRow } from "@mui/material";
import { format } from "date-fns";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";

import JobAction from "./JobAction";

const JobTableItem = ({ row, onItemClick, onDeleteClick }) => {
  const queryClient = useQueryClient();

  const { mutate: updateJobStatus, isPending } = useMutation({
    mutationFn: (d) =>
      axios.put(`${endpoints.connections.updateConnection}${row.id}/`, d),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["connection-list"] });
      queryClient.invalidateQueries({ queryKey: ["connection-count"] });
    },
  });

  const onStatusChange = (newStatus) => {
    updateJobStatus({ connectionStatus: newStatus });
  };

  const showStatusUpdate = row?.sourceConfig?.definitionsName === "BigQuery";

  return (
    <TableRow onClick={onItemClick} sx={{ cursor: "pointer" }}>
      <TableCell>{row?.aiModel?.userModelId}</TableCell>
      <TableCell>{row?.sourceConfig?.definitionsName}</TableCell>
      <TableCell>{format(new Date(row?.created_at), "yyyy-MM-dd")}</TableCell>
      <JobAction
        onDeleteClick={onDeleteClick}
        status={row?.connectionStatus}
        deleted={row?.deleted}
        onStatusChange={showStatusUpdate ? onStatusChange : null}
        statusLoading={isPending}
      />
    </TableRow>
  );
};

JobTableItem.propTypes = {
  row: PropTypes.object,
  onItemClick: PropTypes.func,
  onDeleteClick: PropTypes.func,
};

export default JobTableItem;
