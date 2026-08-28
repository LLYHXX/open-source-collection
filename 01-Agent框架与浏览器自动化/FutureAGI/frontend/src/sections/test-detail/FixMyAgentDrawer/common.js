export const PriorityStatus = {
  HIGH: "high",
  MEDIUM: "medium",
  LOW: "low",
};

export const MetricsTabs = [
  {
    label: "Agent Level",
    value: "agent",
  },
  {
    label: "Branch Level",
    value: "domain",
  },
];

export const LevelType = {
  AGENT: "agent",
  DOMAIN: "domain",
};

export const FixMyAgentDrawerSections = {
  SUGGESTIONS: "suggestions",
  OPTIMIZE: "optimize",
  NONE: "none",
  TRIAL_DETAIL: "trial-detail",
};

export const FixMyAgentStatus = {
  PENDING: "pending",
  RUNNING: "running",
  COMPLETED: "completed",
  FAILED: "failed",
};

export const FixMyAgentRefetchStates = [
  FixMyAgentStatus.PENDING,
  FixMyAgentStatus.RUNNING,
];

export const AgentPromptOptimizerStatus = {
  PENDING: "pending",
  RUNNING: "running",
  COMPLETED: "completed",
  FAILED: "failed",
};

export const AgentPromptOptimizerRefetchStates = [
  AgentPromptOptimizerStatus.PENDING,
  AgentPromptOptimizerStatus.RUNNING,
];

export const AgentPromptOptimizerRerunStatus = [
  AgentPromptOptimizerStatus.FAILED,
  AgentPromptOptimizerStatus.COMPLETED,
];
