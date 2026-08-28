const dataTypeMapping = {
  "Pass/Fail": "bool",
  score: "float",
  choices: "array",
  str_list: "array",
};
export const RIGHT_SECTION_TABS = {
  CALL_ANALYTICS: "callAnalytics",
  EVALUATIONS: "evaluations",
  ANNOTATIONS: "annotations",
};
export const LEFT_SECTION_TABS = {
  TRANSCRIPT: "transcript",
  MESSAGES: "messages",
  ATTRIBUTES: "attributes",
  LOGS: "logs",
  TRACES: "traces",
};
export const TEST_DETAIL_RIGHT_TABS = {
  CALL_ANALYTICS: "callAnalytics",
  EVALUATIONS: "evaluations",
  FLOW_ANALYSIS: "flowAnalysis",
  ANNOTATIONS: "annotations",
};

export const transformEvalMetrics = (evalOutputs) => {
  const evalMetrics = Object.entries(evalOutputs || {}).reduce(
    (acc, [id, item]) => {
      const dataType = dataTypeMapping[item?.outputType];
      return {
        ...acc,
        [id]: {
          name: item.name,
          score:
            dataType === "float"
              ? item.output
              : dataType === "bool"
                ? item.output?.includes("Fail")
                  ? 0
                  : 100
                : item.output,
          explanation: item?.reason,
          loading: item?.loading,
          error: item?.error,
          outputType: dataType,
        },
      };
    },
    {},
  );
  return evalMetrics;
};

export const extractCostBreakdown = (data) => {
  if (!data) return null;
  return {
    llm: {
      cost: data?.llm ?? 0,
      promptTokens: data?.llmPromptTokens,
      completionTokens: data?.llmCompletionTokens,
    },
    stt: {
      cost: data?.stt ?? 0,
    },
    tts: {
      cost: data?.tts ?? 0,
    },
  };
};

export const extractLatencies = (data) => {
  if (!data) return null;
  return {
    endpointing: data?.endpointingLatencyAverage,
    model: data?.modelLatencyAverage,
    voice: data?.voiceLatencyAverage,
    transcriber: data?.transcriberLatencyAverage,
  };
};
