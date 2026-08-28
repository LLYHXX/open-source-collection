import React, { useState } from "react";
import DataTable from "./DataTable";
import { Box, Chip, Typography } from "@mui/material";

const meta = {
  component: DataTable,
  title: "Components/DataTable",
  tags: ["autodocs"],
  parameters: {
    docs: {
      description: {
        component:
          "A lightweight, reusable table built on MUI Table. " +
          "Matches the ag-theme-quartz styling. Supports pagination, " +
          "row selection, custom cell renderers, and loading states.",
      },
    },
  },
};

export default meta;

// ---------------------------------------------------------------------------
// Sample data
// ---------------------------------------------------------------------------
const sampleRows = Array.from({ length: 25 }, (_, i) => ({
  id: `row-${i + 1}`,
  name: `Item ${i + 1}`,
  status: ["Active", "Inactive", "Pending"][i % 3],
  created_at: new Date(2026, 2, 1 + i).toISOString(),
  score: Math.round(Math.random() * 100),
}));

const sampleColumns = [
  {
    id: "name",
    headerName: "Name",
    field: "name",
    flex: 2,
    minWidth: 200,
  },
  {
    id: "status",
    headerName: "Status",
    field: "status",
    flex: 1,
    minWidth: 120,
    renderCell: ({ value }) => (
      <Chip
        label={value}
        size="small"
        color={
          value === "Active"
            ? "success"
            : value === "Pending"
              ? "warning"
              : "default"
        }
        variant="outlined"
      />
    ),
  },
  {
    id: "created_at",
    headerName: "Created",
    field: "created_at",
    flex: 1,
    minWidth: 160,
    valueFormatter: (v) => (v ? new Date(v).toLocaleDateString("en-US") : "-"),
  },
  {
    id: "score",
    headerName: "Score",
    field: "score",
    flex: 1,
    minWidth: 100,
    valueFormatter: (v) => (v != null ? `${v}%` : "-"),
  },
];

// ---------------------------------------------------------------------------
// Stories
// ---------------------------------------------------------------------------

export const Default = {
  args: {
    columns: sampleColumns,
    rows: sampleRows.slice(0, 10),
    page: 1,
    pageSize: 10,
    totalPages: 3,
  },
};

export const Loading = {
  args: {
    columns: sampleColumns,
    rows: [],
    loading: true,
    skeletonRows: 5,
  },
};

export const Empty = {
  args: {
    columns: sampleColumns,
    rows: [],
    emptyTitle: "No items found",
    emptyDescription: "Try adjusting your filters.",
  },
};

export const WithSelection = {
  render: () => {
    const [selected, setSelected] = useState(new Set());
    const [page, setPage] = useState(1);
    const pageSize = 10;
    const start = (page - 1) * pageSize;
    const pageRows = sampleRows.slice(start, start + pageSize);

    return (
      <Box sx={{ height: 500 }}>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Selected: {selected.size} items
        </Typography>
        <DataTable
          columns={sampleColumns}
          rows={pageRows}
          selectable
          selectedIds={selected}
          onSelectionChange={setSelected}
          page={page}
          pageSize={pageSize}
          totalPages={Math.ceil(sampleRows.length / pageSize)}
          onPageChange={setPage}
          onPageSizeChange={() => {}}
        />
      </Box>
    );
  },
};

export const CustomRowHeight = {
  args: {
    columns: sampleColumns,
    rows: sampleRows.slice(0, 5),
    rowHeight: 80,
    page: 1,
    pageSize: 10,
    totalPages: 1,
  },
};
