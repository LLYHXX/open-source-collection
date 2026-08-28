/**
 * Extract tool calls from a span's output, supporting multiple LLM providers.
 * Supports: OpenAI, Anthropic, Bedrock Converse, Google GenAI.
 */
export function extractToolCalls(span) {
  const toolCalls = [];

  let output = span?.output;
  if (!output) return toolCalls;
  if (typeof output === "string") {
    try {
      output = JSON.parse(output);
    } catch {
      return toolCalls;
    }
  }

  // OpenAI-compatible: choices[].message.tool_calls
  if (Array.isArray(output?.choices)) {
    for (const choice of output.choices) {
      const tcList = choice?.message?.tool_calls;
      if (Array.isArray(tcList)) {
        for (const tc of tcList) {
          let args = tc?.function?.arguments;
          if (typeof args === "string") {
            try {
              args = JSON.parse(args);
            } catch {
              /* keep as string */
            }
          }
          toolCalls.push({
            id: tc.id || null,
            functionName: tc?.function?.name || "unknown",
            argumentsObj: typeof args === "object" && args !== null ? args : {},
          });
        }
      }
    }
  }

  // Anthropic: content[] with type "tool_use"
  if (toolCalls.length === 0 && Array.isArray(output?.content)) {
    for (const item of output.content) {
      if (item?.type === "tool_use") {
        toolCalls.push({
          id: item.id || null,
          functionName: item.name || "unknown",
          argumentsObj: item.input || {},
        });
      }
    }
  }

  // Bedrock Converse: output.message.content[] with toolUse
  if (
    toolCalls.length === 0 &&
    Array.isArray(output?.output?.message?.content)
  ) {
    for (const item of output.output.message.content) {
      if (item?.toolUse) {
        toolCalls.push({
          id: item.toolUse.toolUseId || null,
          functionName: item.toolUse.name || "unknown",
          argumentsObj: item.toolUse.input || {},
        });
      }
    }
  }

  // Google GenAI: candidates[].content.parts[] with functionCall
  if (toolCalls.length === 0 && Array.isArray(output?.candidates)) {
    for (const candidate of output.candidates) {
      if (Array.isArray(candidate?.content?.parts)) {
        for (const part of candidate.content.parts) {
          if (part?.functionCall) {
            toolCalls.push({
              id: null,
              functionName: part.functionCall.name || "unknown",
              argumentsObj: part.functionCall.args || {},
            });
          }
        }
      }
    }
  }

  return toolCalls;
}

/**
 * Extract tool definitions from a span's input, supporting multiple LLM providers.
 * Supports: OpenAI, Anthropic, Bedrock Converse, Google GenAI.
 */
export function extractToolDefinitions(span) {
  const toolDefs = [];

  let input = span?.input;
  if (!input) return toolDefs;
  if (typeof input === "string") {
    try {
      input = JSON.parse(input);
    } catch {
      return toolDefs;
    }
  }

  // OpenAI-compatible: tools[] with {type: "function", function: {name, description, parameters}}
  if (Array.isArray(input?.tools)) {
    for (const tool of input.tools) {
      if (tool?.function) {
        toolDefs.push({
          name: tool.function.name || "unknown",
          description: tool.function.description || "",
          parameters: tool.function.parameters || {},
        });
      } else if (tool?.name) {
        // Anthropic format: {name, description, input_schema}
        toolDefs.push({
          name: tool.name,
          description: tool.description || "",
          parameters: tool.input_schema || {},
        });
      } else if (Array.isArray(tool?.functionDeclarations)) {
        // Google GenAI: tools[] with functionDeclarations[]
        for (const fd of tool.functionDeclarations) {
          toolDefs.push({
            name: fd.name || "unknown",
            description: fd.description || "",
            parameters: fd.parameters || {},
          });
        }
      }
    }
  }

  // Bedrock Converse: toolConfig.tools[] with toolSpec
  if (toolDefs.length === 0 && Array.isArray(input?.toolConfig?.tools)) {
    for (const tool of input.toolConfig.tools) {
      if (tool?.toolSpec) {
        toolDefs.push({
          name: tool.toolSpec.name || "unknown",
          description: tool.toolSpec.description || "",
          parameters: tool.toolSpec.inputSchema?.json || {},
        });
      }
    }
  }

  return toolDefs;
}
