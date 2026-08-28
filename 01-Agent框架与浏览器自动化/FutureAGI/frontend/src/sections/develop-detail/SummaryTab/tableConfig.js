import Progressbar from "./Progressbar";

// Column Definitions
export const metricTabColumnDefs = [
  {
    headerName: "Metrics",
    field: "metric",
    // flex: 1,
    width: 360,
  },
  {
    headerName: "Rows",
    field: "row",
    // flex: 1,
    width: 281,
  },
  {
    headerName: "Average Score",
    field: "score",
    flex: 1,
    cellRenderer: Progressbar,
    cellStyle: {
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
    },
  },
];

// export const evaluationTabColumnDefs = = [
//   {
//     headerName: "Evaluation",
//     field: "metric",
//     flex: 1,
//   },
//   {
//     headerName: "Rows",
//     field: "row",
//     flex: 1,
//   },
//   {
//     headerName: "Average",
//     field: "score",
//     flex: 1,
//     cellStyle: {
//       backgroundColor: `red`
//     }
//   },
//   {
//     headerName: "P5",
//     field: "score",
//     flex: 1,
//   },
//   {
//     headerName: "P10",
//     field: "score",
//     flex: 1,
//   },
//   {
//     headerName: "P20",
//     field: "score",
//     flex: 1,
//   },
//   {
//     headerName: "P30",
//     field: "score",
//     flex: 1,
//   },
//   {
//     headerName: "P40",
//     field: "score",
//     flex: 1,
//   },
//   {
//     headerName: "P50",
//     field: "score",
//     flex: 1,
//   },
//   {
//     headerName: "P60",
//     field: "score",
//     flex: 1,
//   },
//   {
//     headerName: "P70",
//     field: "score",
//     flex: 1,
//   },
//   {
//     headerName: "P80",
//     field: "score",
//     flex: 1,
//   },
//   {
//     headerName: "P90",
//     field: "score",
//     flex: 1,
//   },
//   {
//     headerName: "P99",
//     field: "score",
//     flex: 1,
//   },
// ];

export const metricDefaultColDef = {
  lockVisible: true,
  sortable: true,
  filter: false,
  resizable: true,
  suppressHeaderMenuButton: true,
  suppressHeaderContextMenu: true,
};

export const evaluationDefaultColDef = {
  lockVisible: true,
  sortable: true,
  filter: false,
  resizable: false,
  suppressHeaderMenuButton: true,
  suppressHeaderContextMenu: true,
};
