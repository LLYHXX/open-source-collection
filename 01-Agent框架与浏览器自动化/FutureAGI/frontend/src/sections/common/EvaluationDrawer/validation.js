import * as z from "zod";

export const evalsFilterSchema = z.object({
  searchTerm: z.string().optional(),
  selectedUseCases: z.array(z.string()).optional(),
  selectedEvalTags: z.array(z.string()).optional(),
  selectedEvalCategory: z
    .enum(["futureagi_built", "user_built", ""])
    .optional(),
});

export const excludedEvals = [
  "Agent as a Judge",
  "Deterministic Evals",
  "Score Eval",
  "Ends With",
  "Answer Similarity",
  "Contains Any",
  "Contains",
  "Length Greater than",
  "Json Scheme Validation",
  "Custom Code Evaluation",
  "Length Between",
  "API Call",
  "Starts With",
  "Regex",
  "Contains None",
  "Length Less Than",
  "Contains All",
  "Equals",
  "Eval Image Instruction (text to image)",
  "Eval Audio Description",
  "Eval Output",
  "Eval Context Retrieval Quality",
];

export const FUTUREAGI_LLM_MODELS = [
  {
    label: "TURING_LARGE",
    value: "turing_large",
    description:
      "Flagship evaluation model that delivers best-in-class accuracy across multimodal inputs (text, images, audio).",
    allowedDataTypes: [
      "text",
      "boolean",
      "array",
      "float",
      "integer",
      "json",
      "audio",
      "image",
      "document",
      "images",
    ],
  },
  {
    label: "TURING_SMALL",
    value: "turing_small",
    description:
      "Compact variant that preserves high evaluation fidelity for text and images while lowering computational cost.",
    allowedDataTypes: [
      "text",
      "boolean",
      "array",
      "float",
      "integer",
      "json",
      "image",
      "document",
      "images",
    ],
  },
  {
    label: "TURING_FLASH",
    value: "turing_flash",
    description:
      "Latency-optimised version of TURING, providing high-accuracy assessments for text and image inputs with fast response times.",
    allowedDataTypes: [
      "text",
      "boolean",
      "array",
      "float",
      "integer",
      "json",
      "image",
      "document",
      "images",
    ],
  },
  {
    label: "PROTECT",
    value: "protect",
    description:
      "Real-time guardrailing model. Offers very low latency on text and permits user-defined rule sets.",
    allowedDataTypes: [
      "text",
      "boolean",
      "array",
      "float",
      "integer",
      "json",
      "image",
      "audio",
      "images",
    ],
  },
  {
    label: "PROTECT_FLASH",
    value: "protect_flash",
    description:
      "Ultra-fast binary guardrail for text content. Designed for first-pass filtering where millisecond-level turnaround is critical.",
    allowedDataTypes: ["text", "boolean", "array", "float", "integer", "json"],
  },
];

export const FUNCTION_BASE_EVALS = [
  {
    label: "is_json",
    value: "is_json",
  },
  {
    label: "ends_with",
    value: "ends_with",
  },
  {
    label: "equals",
    value: "equals",
  },
  {
    label: "contains_all",
    value: "contains_all",
  },
  {
    label: "length_less_than",
    value: "length_less_than",
  },
  {
    label: "contains_none",
    value: "contains_none",
  },
  {
    label: "regex",
    value: "regex",
  },
  {
    label: "starts_with",
    value: "starts_with",
  },
  {
    label: "api_call",
    value: "api_call",
  },
  {
    label: "length_between",
    value: "length_between",
  },
  {
    label: "custom_code_evaluation",
    value: "custom_code_evaluation",
  },
  {
    label: "json_scheme_validation",
    value: "json_scheme_validation",
  },
  {
    label: "one_line",
    value: "one_line",
  },
  {
    label: "contains_valid_link",
    value: "contains_valid_link",
  },
  {
    label: "is_email",
    value: "is_email",
  },
  {
    label: "no_invalid_links",
    value: "no_invalid_links",
  },
  {
    label: "answer_similarity",
    value: "answer_similarity",
  },
];

export const useCases = [
  {
    icon: "red_teaming",
    title: "Red Teaming",
    value: "RED_TEAMING",
  },
  {
    icon: "retrieval_systems",
    title: "Retrieval Systems",
    value: "RETRIEVAL_SYSTEMS",
  },
  {
    icon: "harmful_objects",
    title: "Harmful Objects",
    value: "HARMFUL_OBJECTS",
  },
  {
    icon: "chatbot_behaviors",
    title: "Chatbot Behaviors",
    value: "CHATBOT_BEHAVIORS",
  },
  {
    icon: "output_format",
    title: "Output Format",
    value: "OUTPUT_FORMAT",
  },
  {
    icon: "nlp_metrics",
    title: "NLP Metrics",
    value: "NLP_METRICS",
  },
  {
    icon: "data_leakage",
    title: "Data Leakage",
    value: "DATA_LEAKAGE",
  },
  {
    icon: "output_validation",
    title: "Output Validation",
    value: "OUTPUT_VALIDATION",
  },
  {
    icon: "image",
    title: "Image",
    value: "IMAGE",
  },
  {
    icon: "audio",
    title: "Audio",
    value: "AUDIO",
  },
  {
    icon: "medical",
    title: "Medical",
    value: "MEDICAL",
  },
  {
    icon: "finance",
    title: "Finance",
    value: "FINANCE",
  },
  {
    icon: "agents",
    title: "Agents",
    value: "AGENTS",
  },
];

export const EvalTypes = [
  { label: "Conversation", value: "CONVERSATION" },
  { label: "Image", value: "IMAGE" },
  // { label: "Future Evals", value: "FUTURE_EVALS" },
  { label: "LLMs", value: "LLMS" },
  { label: "Custom", value: "CUSTOM" },
  { label: "Function", value: "FUNCTION" },
  { label: "Rag", value: "RAG" },
  { label: "Safety", value: "SAFETY" },
  { label: "Hallucination", value: "HALLUCINATION" },
  { label: "Text", value: "TEXT" },
  { label: "Audio", value: "AUDIO" },
];
