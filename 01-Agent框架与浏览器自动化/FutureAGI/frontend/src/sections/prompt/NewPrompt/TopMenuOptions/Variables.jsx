import React, { useState, useRef } from "react";
import { Box, Button, Drawer, Typography } from "@mui/material";
import Iconify from "src/components/iconify";
import PropTypes from "prop-types";
import axios, { endpoints } from "src/utils/axios";
import { useMutation } from "@tanstack/react-query";
import { ConfirmDialog } from "src/components/custom-dialog";
import { LoadingButton } from "@mui/lab";
import { enqueueSnackbar } from "notistack";
import ImportDataset from "./ImportDataset";
import DrawerHeaderbar from "./DrawerHeaderbar";
import VariablesTable from "./Variables/VariablesTable";
import NoVariables from "./Variables/NoVariables";
import { useBeforeUnload } from "src/hooks/useBeforeUnload";

const Variables = (props) => {
  const {
    variables,
    onClose,
    setExtractedVars,
    appliedVariableData,
    setAppliedVariableData,
    handleLabelsAdd,
    currentTitle,
  } = props;

  const [open, setOpen] = useState(false);
  const [openDelete, setOpenDelete] = useState(false);
  const [selected, setSelected] = useState([]);
  const [generatedData, setGeneratedData] = useState([]);
  const [openReload, setOpenReload] = useState(false);
  const gridRef = useRef(null);

  const { mutate: generateData, isPending } = useMutation({
    mutationFn: () =>
      axios.post(endpoints.develop.runPrompt.generateVariables, {
        prompt_name: currentTitle,
        variable_names: variables,
      }),
    onSuccess: (data) => {
      const variablesData = data?.data?.result?.variables;
      const values = Object.values(variablesData ?? {});
      const keys = Object.keys(variablesData ?? {});
      const totalInputs = values[0];
      if (totalInputs?.length > 0) {
        const row = [];
        for (let i = 0; i < totalInputs?.length; i++) {
          const entry = {};
          for (let j = 0; j < values.length; j++) {
            entry[keys[j]] = values[j][i];
          }
          row.push(entry);
        }
        const rows = row.map((item, index) => ({ ...item, id: index }));
        setGeneratedData(rows);
      }
    },
    onError: () => {
      enqueueSnackbar("something went wrong", { variant: "error" });
    },
  });

  // useEffect(() => {
  //   if (variablesData) {
  //     setAppliedVariableData(variablesData);
  //   }
  // }, [variablesData]);

  const onSelectionChanged = (event) => {
    if (!event) {
      setTimeout(() => {
        setSelected([]);
      }, 300);
      gridRef?.current?.api?.deselectAll();
      return;
    }
    const rowId = event.data.id;

    setSelected((prevSelectedItems) => {
      const updatedSelectedRowsData = [...prevSelectedItems];

      const rowIndex = updatedSelectedRowsData.findIndex(
        (row) => row.id === rowId,
      );

      if (rowIndex === -1) {
        updatedSelectedRowsData.push(event.data);
      } else {
        updatedSelectedRowsData.splice(rowIndex, 1);
      }

      return updatedSelectedRowsData;
    });
  };

  const deleteModels = () => {
    const selectedSet = new Set(selected.map((temp) => temp.id));
    setAppliedVariableData(
      Object.fromEntries(
        Object.entries(appliedVariableData).map(([key, value]) => [
          key,
          value.filter((_, ind) => !selectedSet.has(ind)),
        ]),
      ),
    );
    // setOpenDelete(false);
    // onSelectionChanged(null);
  };

  useBeforeUnload(isPending);

  return (
    <Box
      sx={{
        padding: "16px 0 20px 0",
        display: "flex",
        flexDirection: "column",
        height: "100%",
      }}
    >
      <DrawerHeaderbar
        title="Variables"
        onClose={() => (isPending ? setOpenReload(true) : onClose())}
        actionButton={
          variables.length > 0 && (
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                flex: "1",
                gap: "20px",
                justifyContent: "flex-end",
              }}
            >
              {selected?.length > 0 ? (
                <Box
                  sx={{
                    padding: "6px 16px",
                    gap: "16px",
                    borderRadius: "8px",
                    border: "1px solid",
                    borderColor: "divider",
                    display: "flex",
                  }}
                >
                  <Typography
                    sx={{
                      fontSize: "14px",
                      fontWeight: 500,
                      lineHeight: "22px",
                      color: "rgba(120, 87, 252, 1)",
                      paddingRight: "16px",
                      borderRight: "2px solid",
                      borderRightColor: "divider",
                    }}
                  >
                    {selected?.length || 0} Selected
                  </Typography>
                  <Typography
                    sx={{
                      fontSize: "14px",
                      fontWeight: 600,
                      color: "text.secondary",
                      display: "flex",
                      alignItems: "center",
                      gap: "5px",
                      cursor: "pointer",
                    }}
                    onClick={() => setOpenDelete(true)}
                  >
                    <Iconify icon="solar:trash-bin-trash-bold" />
                    Delete
                  </Typography>

                  <Typography
                    sx={{
                      fontSize: "14px",
                      fontWeight: 600,
                      color: "text.secondary",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      cursor: "pointer",
                    }}
                    onClick={() => onSelectionChanged(null)}
                  >
                    Cancel
                  </Typography>
                </Box>
              ) : (
                <Box sx={{ display: "flex", gap: "10px" }}>
                  <LoadingButton
                    startIcon={<Iconify icon="mingcute:pencil-2-ai-line" />}
                    loading={isPending}
                    disabled={isPending}
                    onClick={generateData}
                    sx={{
                      fontSize: 12,
                      fontWeight: 600,
                      paddingLeft: 2,
                      paddingRight: 2,
                      fontFamily: "IBM Plex Sans, sans-serif",
                      color: "#A792FD",
                      backgroundColor: "rgba(120, 87, 252, 0.16)",
                      boxShadow: "none",
                      borderRadius: "10px",
                      lineHeight: 1,
                      "&:hover": {
                        backgroundColor: "rgba(120, 87, 252, 0.32)",
                        boxShadow: "none",
                      },
                      "&:active": {
                        boxShadow: "none",
                      },
                      "&.Mui-disabled": {
                        backgroundColor: "rgba(0, 0, 0, 0.12)",
                      },
                      textTransform: "none",
                    }}
                  >
                    Generate Data
                  </LoadingButton>
                  <Button
                    variant="contained"
                    color="primary"
                    sx={{ minWidth: "150px" }}
                    size="small"
                    onClick={() =>
                      isPending ? setOpenReload(true) : setOpen(true)
                    }
                  >
                    Import data
                  </Button>
                </Box>
              )}
            </Box>
          )
        }
      />

      {!variables.length ? (
        <NoVariables />
      ) : (
        <VariablesTable
          variableNames={variables}
          setExtractedVars={setExtractedVars}
          appliedVariableData={appliedVariableData}
          setAppliedVariableData={setAppliedVariableData}
          handleLabelsAdd={handleLabelsAdd}
          onClose={onClose}
          gridRef={gridRef}
          onSelectionChanged={onSelectionChanged}
          openDelete={openDelete}
          setOpenDelete={setOpenDelete}
          selected={selected}
          generatedData={generatedData}
          isPending={isPending}
          setOpenReload={setOpenReload}
        />
      )}

      <Drawer
        anchor="right"
        open={open}
        onClose={() => setOpen(false)}
        PaperProps={{
          sx: {
            height: "100vh",
            width: "700px",
            position: "fixed",
            zIndex: 9999,
            borderRadius: "10px",
            backgroundColor: "background.paper",
          },
        }}
        ModalProps={{
          BackdropProps: {
            style: { backgroundColor: "transparent" },
          },
        }}
      >
        <ImportDataset
          onClose={() => setOpen(false)}
          variables={variables}
          setAppliedVariableData={setAppliedVariableData}
          setExtractedVars={setExtractedVars}
        />
      </Drawer>
      <ConfirmDialog
        open={openDelete}
        onClose={() => setOpenDelete(false)}
        title="Confirm action"
        content="Are you sure want to delete the selected row?"
        action={
          <LoadingButton
            variant="contained"
            color="error"
            onClick={deleteModels}
            loading={false}
          >
            Delete
          </LoadingButton>
        }
      />
      <ConfirmDialog
        open={openReload}
        onClose={() => setOpenReload(false)}
        title="Data generation in progress"
        content="Are you sure you want to leave?"
        action={
          <LoadingButton
            variant="contained"
            color="error"
            onClick={onClose}
            loading={false}
          >
            Close
          </LoadingButton>
        }
      />
    </Box>
  );
};

Variables.propTypes = {
  variables: PropTypes.arrayOf(PropTypes.string).isRequired,
  onClose: PropTypes.func.isRequired,
  setExtractedVars: PropTypes.any,
  appliedVariableData: PropTypes.any,
  setAppliedVariableData: PropTypes.any,
  handleLabelsAdd: PropTypes.func,
  currentTitle: PropTypes.string,
};

export default Variables;
