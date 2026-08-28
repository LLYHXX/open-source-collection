import { format } from "date-fns";
import { typography } from "src/theme/typography";
import LevelRenderer from "./CellRenderers/LevelRenderer";
import CategoryRenderer from "./CellRenderers/CategoryRenderer";

export const CallDetailLogColumnDefs = [
  {
    headerName: "Timestamp",
    field: "logged_at",
    valueFormatter: ({ value }) => {
      if (!value) return "";
      try {
        return format(new Date(value), "MM/dd/yyyy, hh:mm a").toLowerCase();
      } catch (e) {
        return value;
      }
    },
    width: 180,
    cellStyle: {
      ...typography.s1,
    },
  },
  {
    headerName: "Level",
    field: "severity_text",
    width: 80,
    cellRenderer: LevelRenderer,
  },
  {
    headerName: "Category",
    field: "category",
    width: 100,
    cellRenderer: CategoryRenderer,
  },
  {
    headerName: "Raw Data",
    field: "attributes",
    valueFormatter: ({ value, data }) => {
      if (!value) return "";
      return JSON.stringify(data);
    },
    cellStyle: {
      whiteSpace: "normal",
      display: "-webkit-box",
      WebkitLineClamp: 2,
      WebkitBoxOrient: "vertical",
      overflow: "hidden",
      textOverflow: "ellipsis",
      ...typography.s1,
      height: "100%",
    },
  },
];

export const LogDetailDrawerColumnDefs = [
  {
    headerName: "Key",
    field: "key",
  },
  {
    headerName: "Value",
    field: "value",
    flex: 1,
  },
];

export const LevelOptions = [
  {
    label: "Log",
    value: "LOG",
  },
  {
    label: "Info",
    value: "INFO",
  },
  {
    label: "Warning",
    value: "WARN",
  },
  {
    label: "Error",
    value: "ERROR",
  },
];

export const CategoryOptions = [
  {
    label: "System",
    value: "system",
  },
  {
    label: "Voice",
    value: "voice",
  },
  {
    label: "Transcriber",
    value: "transcriber",
  },
  {
    label: "Endpointing",
    value: "endpointing",
  },
  {
    label: "Model",
    value: "model",
  },
  {
    label: "Latency",
    value: "latency",
  },
  {
    label: "Transport",
    value: "transport",
  },
  {
    label: "Webhook",
    value: "webhook",
  },
];
