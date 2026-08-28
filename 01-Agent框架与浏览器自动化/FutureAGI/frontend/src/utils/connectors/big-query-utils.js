export const getMappedData = (connMappings, tags) => {
  const finalArr = [];
  if (!connMappings || Object.keys(connMappings).length === 0) {
    return finalArr;
  }
  finalArr.push({
    input: "connection_id",
    output: connMappings.conversationId,
  });
  finalArr.push({ input: "timestamp", output: connMappings.timestamp });
  connMappings.prompt.forEach((p, i) => {
    const key = `model_input_${p.type}_${i + 1}`;
    finalArr.push({ input: key, output: p.columnName });
  });
  connMappings.response.forEach((p, i) => {
    const key = `model_output_${p.type}_${i + 1}`;
    finalArr.push({ input: key, output: p.columnName });
  });
  if (tags && tags?.length) {
    tags.forEach((tag, i) => {
      finalArr.push({ input: `tag_${i + 1}`, output: tag });
    });
  }
  if (connMappings?.promptTemplate) {
    finalArr.push({
      input: "prompt_template",
      output: connMappings?.promptTemplate,
    });
  }
  if (connMappings?.context) {
    finalArr.push({
      input: "context",
      output: connMappings?.context,
    });
  }
  if (connMappings?.variables?.length) {
    const vars =
      typeof connMappings?.variables === "string"
        ? connMappings?.variables?.split(",")
        : connMappings?.variables;
    vars.forEach((variable) => {
      finalArr.push({ input: variable, output: variable });
    });
  }
  return finalArr;
};
