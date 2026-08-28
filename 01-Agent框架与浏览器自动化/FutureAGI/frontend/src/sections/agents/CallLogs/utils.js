export const transformMetricDetails = (data) => {
  const {
    eval_outputs: evalOutputs,
    vapi_call_data: vapiCallData,
    duration_seconds: durationSeconds,
    transcripts,
    scenario_name: scenarioName,
    customer_number: customerNumber,
    call_metadata: callMetadata,
    created_at: createdAt,
    ...rest
  } = data ?? {};
  const metricDetails = {
    ...rest,
    transcript: transcripts,
    audioUrl: data?.recording_url,
    recordings: vapiCallData?.recording,
    duration: durationSeconds,
    scenario: scenarioName,
    customerName: customerNumber,
    timestamp: createdAt,
    scenarioColumns: {
      outcome: {
        columnName: "outcome",
        value: callMetadata?.row_data?.outcome,
      },
      situation: {
        columnName: "situation",
        value: callMetadata?.row_data?.situation,
      },
      persona: {
        columnName: "persona",
        value: callMetadata?.row_data?.persona,
      },
    },
  };
  const evalMetrics = Object.entries(evalOutputs || {}).reduce(
    (acc, [id, metric]) => {
      const { output, output_type, ...rest } = metric;
      acc[id] = {
        ...rest,
        value: output,
        type: output_type,
      };
      return acc;
    },
    {},
  );
  return {
    metricDetails,
    evalMetrics,
  };
};
/**
 * `agent_talk_percentage` is a system metric column, not a span attribute.
 * The backend uses `col_type` to route the filter to the correct handler —
 * span attributes go through one path, system metrics through another.
 * Since the grid filter model does not include schema type information,
 * we must explicitly set `col_type: "SYSTEM_METRIC"` for this column
 * before sending the request. All other columns are span attributes and
 * are handled correctly by the backend without any override.
 */
// All voice system metrics now use SYSTEM_METRIC col_type via
// FilterColTypes in constants.js — no per-filter override needed.
export const patchSystemMetricFilters = (params) => params;
