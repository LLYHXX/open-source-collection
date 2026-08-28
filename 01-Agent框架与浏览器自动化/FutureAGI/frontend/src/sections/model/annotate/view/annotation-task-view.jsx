import React from "react";
import { Container, Stack, Typography } from "@mui/material";
import { useAnnotationTasks } from "src/api/annotation/annotation";
import EmptyContent from "src/components/empty-content";
import { useSettingsContext } from "src/components/settings";
import { useTable } from "src/components/table";
import AnnotationTaskTable from "../annotation-task-table";

export default function AnnotationTaskView() {
  const table = useTable({ defaultRowsPerPage: 10 });

  const settings = useSettingsContext();

  const { tasks } = useAnnotationTasks(null, table.page + 1);

  const notFound = !tasks.length || !tasks.length;

  return (
    <>
      <Container maxWidth={settings.themeStretch ? false : "lg"}>
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
        >
          <Typography variant="h4">Tasks</Typography>
        </Stack>

        {notFound ? (
          <EmptyContent
            filled
            title="No Data"
            sx={{
              py: 10,
            }}
          />
        ) : (
          <>
            <AnnotationTaskTable
              table={table}
              tableData={tasks}
              // dataFiltered={dataFiltered}
              // onDeleteRow={handleDeleteItem}
              // notFound={notFound}
              // onOpenConfirm={confirm.onTrue}
            />
          </>
        )}
      </Container>
    </>
  );
}
