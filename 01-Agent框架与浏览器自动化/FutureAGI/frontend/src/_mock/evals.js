export const evals = [
  {
    title: "Answer Completeness",
    subtitle: "Checks if the response answers the user's query completely.",
    tags: ["LLM"],
  },
  {
    title: "API Call",
    subtitle: "Makes an API call and checks the response",
    tags: ["Function"],
  },
  {
    title: "Contains",
    subtitle: "Checks if the response contains the provided keyword",
    tags: ["Function"],
  },
  {
    title: "Contains All",
    subtitle: "Checks if the response contains all provided keywords",
    tags: ["Function"],
  },
  {
    title: "Contains Any",
    subtitle: "Checks if the response contains any of the following keywords",
    tags: ["Function"],
  },
  {
    title: "Contains Email",
    subtitle: "Checks if the response contains an email",
    tags: ["Function"],
  },
  {
    title: "Contains JSON",
    subtitle: "Checks if the response contains a JSON",
    tags: ["Function"],
  },
  {
    title: "Contains Link",
    subtitle: "Checks if the response contains a link",
    tags: ["Function"],
  },
  {
    title: "Contains None",
    subtitle:
      "Checks if the response does not contain any of the provided keywords",
    tags: ["Function"],
  },
  {
    title: "Contains Valid Link",
    subtitle: "Checks if the response contains a valid link",
    tags: ["Function"],
  },
  {
    title: "Context Sufficiency",
    subtitle:
      "Checks if the context contains enough information to answer the user's query",
    tags: ["LLM"],
  },
  {
    title: "Conversation Coherence",
    subtitle:
      "Checks if every message in the conversation was coherent given the previous messages.",
    tags: ["LLM"],
  },
  {
    title: "Conversation Resolution",
    subtitle: "Checks if the conversation was successfully resolved",
    tags: ["LLM"],
  },
  {
    title: "Custom Code Evaluation",
    subtitle: "Evaluate using the code provided",
    tags: ["Function"],
  },
  {
    title: "Custom Prompt",
    subtitle: "Evaluates the response using a custom prompt",
    tags: ["LLM"],
  },
];
