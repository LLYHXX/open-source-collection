import { format } from "date-fns";
import AnnotationValueCellRenderer from "../CustomRenderer/AnnotationValueCellRenderer";
import AnnotatorCellRenderer from "../CustomRenderer/AnnotatorCellRenderer";
import { NotesCellRenderer } from "../CustomRenderer/NotesCellRenderer";

export const getAnnotationColumns = () => [
  {
    id: "annotation_name",
    name: "Annotation Name",
    field: "annotation_name",
    isVisible: true,
    flex: 1,
    headerName: "Annotation Name",
  },
  {
    id: "value",
    name: "Value",
    field: "value",
    isVisible: true,
    flex: 1,
    headerName: "Value",
    cellRenderer: AnnotationValueCellRenderer,
  },
  {
    id: "updated_by",
    name: "Updated By",
    field: "updated_by",
    isVisible: true,
    flex: 1,
    headerName: "Updated By",
    cellRenderer: AnnotatorCellRenderer,
  },
  {
    id: "updated_at",
    name: "Updated At",
    field: "updated_at",
    isVisible: true,
    flex: 1,
    headerName: "Updated At",
    valueFormatter: (params) => {
      return format(new Date(params.value), "yy-MM-dd");
    },
  },
];

export const spanNotesColumnsDefs = [
  {
    field: "notes",
    headerName: "Note",
    flex: 2,
    cellRenderer: NotesCellRenderer,
  },
  {
    field: "annotator",
    headerName: "Annotator",
    flex: 1,
    cellRenderer: AnnotatorCellRenderer,
  },
];

export const notesColumnsDefs = [
  {
    id: "notes",
    name: "Notes",
    field: "notes",
    isVisible: true,
    flex: 1,
    headerName: "Notes",
    cellRenderer: NotesCellRenderer,
  },
  {
    id: "created_by_user",
    name: "Created By",
    field: "created_by_user",
    isVisible: true,
    flex: 1,
    headerName: "Created By",
    cellRenderer: AnnotatorCellRenderer,
  },
  {
    id: "created_at",
    name: "Created At",
    field: "created_at",
    isVisible: true,
    flex: 1,
    headerName: "Created At",
    valueFormatter: (params) => {
      return format(new Date(params.value), "yy-MM-dd");
    },
  },
];
