export const numericGraphHeader = [
  { text: "Pearson Correlation (Strong agreement)", valueKey: "correlation" },
  { text: "Mean", valueKey: "avgValue" },
  { text: "Std. deviation", valueKey: "stddevValue" },
  { text: "Range", valueKey: "range" },
];

export const categoricalGraphHeader = [
  { text: "Fleiss’s Kappa (Substancial agreement)", valueKey: "kappa" },
  { text: "Most frequent", valueKey: "modeValue" },
  { text: "Unique labels", valueKey: "numUnique" },
  { text: "Label coverage", valueKey: "labelCoverage" },
];

export const textGraphHeader = [
  {
    text: "Cosine Similarity (Semantic alignment)",
    valueKey: "cosineSimilarity",
  },
  { text: "Avg.", valueKey: "vocabSize" },
  { text: "Vocabulary size", valueKey: "vocabSize" },
  { text: "Length Range", valueKey: "lenRange" },
];

export const thumbsGraphHeader = [
  { text: "Approval rate", valueKey: "" },
  { text: "Rejection rate", valueKey: "" },
  { text: "Sentiment", valueKey: "" },
  { text: "Label coverage ", valueKey: "" },
];

export const starGraphHeader = [
  { text: "Avg. rating", valueKey: "" },
  { text: "Satisfaction rate (4-5 stars)", valueKey: "" },
  { text: "Most common", valueKey: "" },
  { text: "Label coverage ", valueKey: "" },
];
