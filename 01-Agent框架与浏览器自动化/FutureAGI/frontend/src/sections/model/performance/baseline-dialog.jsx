import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import PropTypes from "prop-types";
import React, { useState } from "react";
import {
  updateBaselineDataset,
  useGetModelDataset,
} from "src/api/model/dataset";
import { useSnackbar } from "src/components/snackbar";
import logger from "src/utils/logger";

export default function BaselineDialog({ model, dialog }) {
  const { enqueueSnackbar } = useSnackbar();

  const options = {
    environment: ["Training", "Validation", "Corpus"],
  };
  const { datasets } = useGetModelDataset(model.id, options);

  const [selectedRow, setSelectedRow] = useState(
    datasets?.find((item) => item.isBaseline),
  );

  const handleRowClick = async (row, index) => {
    setSelectedRow({
      row,
      index,
    });
  };

  async function changeBaseline() {
    try {
      await updateBaselineDataset(model.id, { ...selectedRow.row });
      enqueueSnackbar("Update success!");
      dialog.onFalse();
    } catch (error) {
      logger.error("Failed to change baseline", error);
    }
  }

  return (
    <>
      <Dialog open={dialog.value} onClose={dialog.onFalse}>
        <DialogTitle>Choose a baseline dataset</DialogTitle>

        <DialogContent>
          <TableContainer>
            <Table size={"small"}>
              <TableHead>
                <TableRow>
                  <TableCell>Start Date</TableCell>
                  <TableCell>End Date</TableCell>
                  <TableCell>Environment</TableCell>
                  <TableCell>Version</TableCell>
                  <TableCell>Batch name</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {datasets?.map((row, index) => (
                  <TableRow
                    hover
                    selected={selectedRow?.index === index}
                    key={index}
                    sx={{ "&:last-child td, &:last-child th": { border: 0 } }}
                    style={{ cursor: "pointer" }}
                    onClick={() => handleRowClick(row, index)}
                  >
                    <TableCell>{row.startDate}</TableCell>
                    <TableCell>{row.endDate}</TableCell>
                    <TableCell>{row.environment}</TableCell>
                    <TableCell>{row.modelVersion}</TableCell>
                    <TableCell>{row.batchId}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>

        <DialogActions>
          <Button onClick={dialog.onFalse} variant="outlined" color="inherit">
            Cancel
          </Button>
          <Button onClick={changeBaseline} variant="contained">
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

BaselineDialog.propTypes = {
  model: PropTypes.object,
  dialog: PropTypes.object,
};
