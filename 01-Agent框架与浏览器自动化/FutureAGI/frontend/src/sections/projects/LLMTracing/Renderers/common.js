export const HEADER_ICON_CONFIG = {
  "Node Type": {
    type: "iconify",
    icon: "ph:tree-view",
    color: "text.primary",
  },
  "User Email": {
    type: "iconify",
    icon: "mage:email",
    color: "text.primary",
  },
  "User Phone Number": {
    type: "iconify",
    icon: "line-md:phone",
    color: "text.primary",
  },
  "Start Time": {
    type: "iconify",
    icon: "material-symbols:schedule-outline",
    color: "text.primary",
  },
  "Latency (ms)": {
    type: "iconify",
    icon: "material-symbols:schedule-outline",
    color: "text.primary",
  },
  "Total Tokens": {
    type: "svg",
    src: "/assets/icons/ic_tokens_header.svg",
  },
  "Total Cost": {
    type: "svg",
    src: "/assets/icons/components/ic_cost.svg",
  },
  Cost: {
    type: "svg",
    src: "/assets/icons/components/ic_cost.svg",
  },
  "Trace Name": {
    type: "svg",
    src: "/assets/icons/navbar/ic_dash_tasks.svg",
  },
};

export const RENDERER_CONFIG = {
  ignoredQuickFilters: ["input", "output"],
  applyDateFormat: ["start_time", "first_used", "last_used"],
  alignRightItems: [
    "User Phone Number",
    "Start Time",
    "Latency (ms)",
    "Total Tokens",
    "Total Cost",
  ],
  nameColumns: ["trace_name", "span_name", "name"],
  costColumns: ["total_cost", "cost"],
  tokenColumns: ["total_tokens", "prompt_tokens", "completion_tokens"],
  latencyColumns: ["latency", "latency_ms"],
  timestampColumns: ["start_time"],
  tagColumns: ["tags", "labels"],
};

export const CELL_TYPES = {
  PROMPT_VERSION: "prompt_template_version",
  LABELS: "labels",
  STATUS: "status",
  TRACE_ID: "trace_id",
  SPAN_ID: "span_id",
  USER_ID: "user_id",
};
