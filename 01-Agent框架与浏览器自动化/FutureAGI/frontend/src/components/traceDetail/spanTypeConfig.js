/**
 * Shared span type configuration — icons, colors, labels.
 * Used across TraceTreeV2, SpanDetailPane, SpanTreeTimeline, LogViewRow.
 */

export const TYPE_CONFIG = {
  agent: {
    color: "#9333EA",
    icon: "/icons/tracedetails/agent_icon.svg",
    label: "Agent",
    mdiIcon: "mdi:robot-outline",
  },
  chain: {
    color: "#EC4899",
    icon: "/icons/tracedetails/chain_icon.svg",
    label: "Chain",
    mdiIcon: "mdi:link-variant",
  },
  llm: {
    color: "#2563EB",
    icon: "/icons/tracedetails/llm_icon.svg",
    label: "LLM",
    mdiIcon: "mdi:brain",
  },
  generation: {
    color: "#2563EB",
    icon: "/icons/tracedetails/llm_icon.svg",
    label: "Generation",
    mdiIcon: "mdi:brain",
  },
  tool: {
    color: "#F59E0B",
    icon: "/icons/tracedetails/tool_icon.svg",
    label: "Tool",
    mdiIcon: "mdi:wrench-outline",
  },
  retriever: {
    color: "#0D9488",
    icon: "/icons/tracedetails/retriever_icon.svg",
    label: "Retriever",
    mdiIcon: "mdi:database-search-outline",
  },
  embedding: {
    color: "#6366F1",
    icon: "/icons/tracedetails/embedding_icon.svg",
    label: "Embedding",
    mdiIcon: "mdi:vector-combine",
  },
  guardrail: {
    color: "#EF4444",
    icon: "/icons/tracedetails/guardrail_icon.svg",
    label: "Guardrail",
    mdiIcon: "mdi:shield-alert-outline",
  },
  evaluator: {
    color: "#6366F1",
    icon: "/icons/tracedetails/evaluator_icon.svg",
    label: "Evaluator",
    mdiIcon: "mdi:check-decagram-outline",
  },
  conversation: {
    color: "#8B5CF6",
    icon: "/icons/tracedetails/conversation_icon.svg",
    label: "Conversation",
    mdiIcon: "mdi:message-text-outline",
  },
  reranker: {
    color: "#65A30D",
    icon: "/icons/tracedetails/reranker_icon.svg",
    label: "Reranker",
    mdiIcon: "mdi:sort-variant",
  },
  unknown: {
    color: "#94A3B8",
    icon: "/icons/tracedetails/unknown_icon.svg",
    label: "Unknown",
    mdiIcon: "mdi:help-circle-outline",
  },
};

export const getTypeConfig = (type) =>
  TYPE_CONFIG[(type || "").toLowerCase()] || TYPE_CONFIG.unknown;

/**
 * LLM provider icons — shown next to model name.
 */
export const PROVIDER_ICONS = {
  openai: { icon: "simple-icons:openai", color: "text.primary" },
  anthropic: { icon: "simple-icons:anthropic", color: "#D97706" },
  google: { icon: "mdi:google", color: "#4285F4" },
  azure: { icon: "mdi:microsoft-azure", color: "#0078D4" },
  cohere: { icon: "mdi:alpha-c-circle", color: "#39594D" },
  mistral: { icon: "mdi:alpha-m-circle", color: "#F54E42" },
  groq: { icon: "mdi:lightning-bolt", color: "#F55036" },
  bedrock: { icon: "mdi:aws", color: "#FF9900" },
  meta: { icon: "simple-icons:meta", color: "#0668E1" },
  deepseek: { icon: "mdi:brain", color: "#0A84FF" },
};

export const getProviderIcon = (provider) => {
  if (!provider) return null;
  const key = provider.toLowerCase().replace(/[^a-z]/g, "");
  return PROVIDER_ICONS[key] || null;
};
