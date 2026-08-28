import { format } from "date-fns";
import AnnotationsStatusLine from "./AnnotationStatusLine";
import AnnotationAssignedRender from "./AnnotationAssignedRender";
import AnnotationActions from "./AnnotationActions";

// Column Definitions
export const annotationsTabColumnDefs = [
  {
    headerName: "View Name",
    field: "name",
    flex: 1,
    cellStyle: { color: "var(--text-primary)" },
  },
  {
    headerName: "No.of Annotations",
    field: "noOfAnnotations",
    flex: 1,
    cellStyle: { color: "var(--text-primary)" },
  },
  {
    headerName: "Status",
    field: "status",
    flex: 1.5,
    cellRenderer: AnnotationsStatusLine,
    cellStyle: { display: "flex", alignItems: "center" },
  },
  {
    headerName: "People Assigned",
    field: "peopleAssigned",
    flex: 1.5,
    cellRenderer: AnnotationAssignedRender,
    cellStyle: { display: "flex", alignItems: "center" },
  },
  {
    headerName: "Created At",
    field: "created_at",
    flex: 1,
    valueFormatter: (p) => {
      if (!p.value) return ""; // Ensures no errors
      const date = new Date(p.value);
      return isNaN(date.getTime()) ? "" : format(date, "yy-MM-dd");
    },
  },
  {
    headerName: "Actions",
    field: "actions",
    flex: 1,
    cellRenderer: AnnotationActions,
    cellStyle: { display: "flex", alignItems: "center" },
  },
];

export const annotationsDefaultColDef = {
  lockVisible: true,
  sortable: true,
  filter: false,
  resizable: true,
  suppressHeaderMenuButton: true,
  suppressHeaderContextMenu: true,
};
