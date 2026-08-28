import { formatNumberSystem } from "src/utils/utils";

export const annualDiscount = 0.1; // 10% anual discount

export const traceDropdown = [
  { label: "10K", value: 0 },
  { label: "25K", value: 0.025 },
  { label: "50K", value: 0.05 },
  { label: "100K", value: 0.1 },
  { label: "250K", value: 0.25 },
  { label: "1M", value: 1 },
];

export const evaluationDropdown = [
  { label: "10K", value: 10 },
  { label: "50K", value: 50 },
  { label: "100K", value: 100 },
  { label: "500K", value: 500 },
  { label: "1M", value: 1000 },
  { label: "5M", value: 5000 },
];

export const syntheticDropdown = [
  { label: "0.5K", value: 0.5 },
  { label: "1K", value: 1 },
  { label: "2K", value: 2 },
  { label: "5K", value: 5 },
  { label: "10K", value: 10 },
];

export const simulationDropdown = [
  { label: "5K", value: 5 },
  { label: "10K", value: 10 },
  { label: "25K", value: 25 },
  { label: "50K", value: 50 },
];

export const concurrentDropdown = [
  { label: "2", value: 2 },
  { label: "3", value: 3 },
  { label: "4", value: 4 },
  { label: "5", value: 5 },
  { label: "10", value: 10 },
];

export const activePlan = {
  TIER_FREE: "free",
  TIER_BASIC: "basic",
  TIER_BASIC_YEARLY: "basic_yearly",
  TIER_CUSTOM: "custom",
};

export const planData = [
  {
    section: "General",
    features: [
      {
        name: "One time credit",
        free: "$5",
        growth: "$5",
        enterprise: "$5",
      },
      {
        name: "Monthly Credits",
        free: "$0",
        growth: "$20",
        enterprise: "Custom",
      },
      {
        name: "Team members/ Number of seats",
        free: "3 Seats",
        growth: "Unlimited",
        enterprise: "Custom",
      },
      {
        name: "Price Per Extra Seat",
        free: "0",
        growth: "$20",
        enterprise: "Custom",
      },
      {
        name: "Monthly retainer: Usage limits vary by plan. Upgrade required for higher limits",
        free: "0",
        growth: "$50",
        enterprise: "Custom",
      },
      {
        name: "Yearly retainer",
        free: "0",
        growth: "2 months off (16.6%)",
        enterprise: "Custom",
      },
      {
        name: "Single sign on",
        free: false,
        growth: false,
        enterprise: true,
      },
      {
        name: "Role Based Access Control",
        free: false,
        growth: false,
        enterprise: true,
      },
      {
        name: "On-premise deployment option",
        free: false,
        growth: false,
        enterprise: true,
      },
      {
        name: "API Access",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "SLA",
        free: "2-3 days",
        growth: "Business Hours",
        enterprise: "3 hr response window",
      },
      {
        name: "Support channel",
        free: "Community",
        growth: "Email",
        enterprise: "Private Slack Channel and Support engineer",
      },
    ],
  },
  {
    section: "Observe",
    features: [
      {
        name: "LLM Observability",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "Monthly limits on Traces",
        free: "10k traces",
        growth: "Unlimited traces, $8 per 100K traces",
        enterprise: "Unlimited traces, $8 per 100K traces",
      },
      {
        name: "Historical Lookback",
        free: "120 days",
        growth: "360 days",
        enterprise: "Custom",
      },
      {
        name: "Full-Resolution Data Retention",
        free: "120 days",
        growth: "180 days",
        enterprise: "Custom",
      },
      {
        name: "Storage",
        free: "1GB",
        growth: "10 GB",
        enterprise: "Custom Value",
      },
      {
        name: "Protect: Guardrails",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "Evaluation Tasks",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "Custom Metrics builder",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "Sessions",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "Performance Tracing",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "Experiments",
        free: "3",
        growth: "5",
        enterprise: "Unlimited",
      },
      {
        name: "Projects",
        free: "3",
        growth: "5",
        enterprise: "Unlimited",
      },
      {
        name: "Analytics",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "Data Export Limits",
        free: "-",
        growth: "5GB",
        enterprise: "Unlimited",
      },
      {
        name: "Anomaly detection",
        free: false,
        growth: true,
        enterprise: true,
      },
      {
        name: "Outlier Detection",
        free: false,
        growth: true,
        enterprise: true,
      },
      {
        name: "Watchdog: Automated insights",
        free: false,
        growth: true,
        enterprise: true,
      },
      {
        name: "Alerting Integrations",
        free: false,
        growth: true,
        enterprise: true,
      },
      {
        name: "Out of box Dashboards",
        free: false,
        growth: true,
        enterprise: true,
      },
    ],
  },
  {
    section: "Build",
    features: [
      {
        name: "Prompt workbench",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "Prompt Playground: Experiment Side by Side",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "Agentic Based Prompt Optimizer",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "RL based prompt-optimiser",
        free: true,
        growth: true,
        enterprise: "Custom",
      },
      {
        name: "Number of Run Prompts: Use your own API key",
        free: "Unlimited",
        growth: "Unlimited",
        enterprise: "Unlimited",
      },
      {
        name: "Experiments: Use your own API key",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "Number of Experiments: Use your own API key",
        free: "Unlimited",
        growth: "Unlimited",
        enterprise: "Unlimited",
      },
      {
        name: "Winner prompt identifier",
        free: true,
        growth: true,
        enterprise: true,
      },
      {
        name: "Number of Datasets",
        free: "5",
        growth: "20",
        enterprise: "Unlimited",
      },
      {
        name: "Max dataset rows / dataset",
        free: formatNumberSystem(2000),
        growth: formatNumberSystem(100000),
        enterprise: "Unlimited",
      },
      {
        name: "Synthetic Data Generation($100 per Million tokens generated)",
        free: true,
        growth: true,
        enterprise: "Custom",
      },
      {
        name: "Annotations",
        free: "Unlimited",
        growth: "Unlimited",
        enterprise: "Unlimited",
      },
      // {
      //   name: "Auto Annotation ($10 per Million input tokens)",
      //   free: "100 rows",
      //   growth: "10K rows",
      //   enterprise: "Custom",
      // },
      // {
      //   name: "Number of Annotation Jobs",
      //   free: "2",
      //   growth: "10",
      //   enterprise: "Unlimited",
      // },
    ],
  },
  {
    section: "Evals",
    features: [
      {
        name: "Eval: Usage based pricing",
        free: true,
        growth: true,
        enterprise: "Custom  pricing",
      },
      {
        name: "Error Localizer",
        free: false,
        growth: true,
        enterprise: true,
      },
      {
        name: "Feedback on Evals",
        free: false,
        growth: true,
        enterprise: true,
      },
      {
        name: `Evals based on "Knowledge base"`,
        free: false,
        growth: true,
        enterprise: true,
      },
    ],
  },
  {
    section: "Security & Compliance",
    features: [
      {
        name: "Security/ Compliance reporting",
        free: false,
        growth: false,
        enterprise: "SOC-2 Type 2 & ISO certification",
      },
      {
        name: "Hippa Reporting",
        free: false,
        growth: false,
        enterprise: true,
      },
    ],
  },
];
