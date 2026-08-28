import {
  NameCellRenderer,
  DateCellRenderer,
  CollaboratorsCellRenderer,
  HeaderComponent,
} from "./cellRenderers";

// Column definitions for Agent List Grid
export const columnDefs = [
  {
    headerName: "Agent Name",
    field: "name",
    cellRenderer: NameCellRenderer,
    minWidth: 300,
    flex: 2,
    headerComponent: HeaderComponent,
    headerComponentParams: {
      iconSrc: "/assets/icons/navbar/ic_agents.svg",
      label: "Agent Name",
    },
  },
  {
    headerName: "No.of nodes",
    field: "noOfNodes",
    minWidth: 100,
    flex: 1,
    cellStyle: {
      textAlign: "center",
    },
    headerComponent: HeaderComponent,
    headerComponentParams: {
      iconSrc: "/assets/icons/ic_col_header.svg",
      label: "No.of nodes",
    },
  },
  {
    headerName: "Created by",
    field: "createdBy",
    minWidth: 300,
    flex: 2,
    cellStyle: {
      display: "flex",
      paddingInline: "16px",
      justifyContent: "center",
    },
    headerComponent: HeaderComponent,
    headerComponentParams: {
      iconSrc: "/assets/icons/ic_col_header.svg",
      label: "Created by",
    },
  },
  {
    headerName: "Collaborators",
    field: "collaborators",
    cellRenderer: CollaboratorsCellRenderer,
    minWidth: 150,
    flex: 1,
    headerComponent: HeaderComponent,
    headerComponentParams: {
      iconSrc: "/assets/icons/ic_col_header.svg",
      label: "Collaborators",
    },
  },
  {
    headerName: "Created at",
    field: "created",
    cellRenderer: DateCellRenderer,
    minWidth: 150,
    flex: 1,
    headerComponent: HeaderComponent,
    headerComponentParams: {
      iconSrc: "/assets/icons/navbar/ic_new_clock.svg",
      label: "Created at",
    },
  },
  {
    headerName: "Updated at",
    field: "updated",
    cellRenderer: DateCellRenderer,
    minWidth: 150,
    flex: 1,
    headerComponent: HeaderComponent,
    headerComponentParams: {
      iconSrc: "/assets/icons/navbar/ic_new_clock.svg",
      label: "Updated at",
    },
  },
];
