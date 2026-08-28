export const ROLE_OPTIONS = [
  { label: "Owner", value: "Owner" },
  { label: "Admin", value: "Admin" },
  { label: "Member", value: "Member" },
  {
    label: "Viewer",
    value: "Viewer",
  },
  {
    label: "Workspace Admin",
    value: "workspace_admin",
  },
  {
    label: "Workspace Member",
    value: "workspace_member",
  },
  {
    label: "Workspace Viewer",
    value: "workspace_viewer",
  },
];

export const AVAILABLE_ROLES = [
  {
    label: "Data Scientist / ML Engineer",
    value: "Data Scientist / ML Engineer",
  },
  {
    label: "Backend / Platform Engineer / DevOps",
    value: "Backend / Platform Engineer / DevOps",
  },
  { label: "Subject Matter Expert", value: "Subject Matter Expert" },
  { label: "Product Manager / Analyst", value: "Product Manager / Analyst" },
  {
    label: "Customer Success / Business / Operations Manager",
    value: "Customer Success / Business / Operations Manager",
  },
];

export const GOALS_LIST = [
  {
    id: "monitor_llms_agents",
    label: "Monitor LLMs and Agents",
    description:
      "Track performance, reliability, and behavior of your AI systems.",
  },
  {
    id: "run_evaluations",
    label: "Run Evaluations",
    description:
      "Compare models, prompts, or versions and establish benchmarks.",
  },
  {
    id: "simulate_interactions",
    label: "Simulate Voice or Chat Interactions",
    description: "Test how your AI responds in real-world conversations.",
  },
  {
    id: "annotate_improve_data",
    label: "Annotate and Improve Data",
    description:
      "Label, review, and enhance datasets for better model quality.",
  },
  {
    id: "optimize_ai_agents",
    label: "Optimize AI Agents",
    description:
      "Tune responses, workflows, and outcomes for higher accuracy and engagement.",
  },
  {
    id: "analyze_system_health",
    label: "Analyze System Health",
    description: "Understand latency, traces, and cost trends.",
  },
];
export const DEFAULT_ROLES = [
  "Data Scientist / ML Engineer",
  "Backend / Platform Engineer / DevOps",
  "Subject Matter Expert",
  "Product Manager / Analyst",
  "Customer Success / Business / Operations Manager",
];
