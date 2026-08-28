/**
 * Consolidate multi-turn conversation into comprehensive widget prompts.
 *
 * When a user iterates on an analysis widget through multiple chat turns:
 *   Turn 1: "Show me error analysis" → markdown with basic analysis
 *   Turn 2: "Focus on guardrail violations" → refined markdown
 *   Turn 3: "Also mention the input that was blocked" → final version
 *
 * At save time, we consolidate ALL user messages into a single comprehensive
 * prompt for each dynamicAnalysis widget, so replaying on a new trace
 * captures the full intent without needing multi-turn replay.
 */

/**
 * Extract user messages from the Falcon conversation.
 */
function getUserMessages(messages) {
  return (messages || [])
    .filter((m) => m.role === "user" && m.content)
    .map((m) => m.content);
}

/**
 * Build a consolidated analysis prompt from all user messages.
 *
 * Strategy: combine all user instructions into a single prompt that
 * captures the full intent. The first message is the initial request,
 * subsequent messages are refinements.
 */
function buildConsolidatedPrompt(userMessages, originalPrompt) {
  if (!userMessages.length) return originalPrompt;

  // If only 1-2 messages, the original prompt is likely sufficient
  if (userMessages.length <= 2) return originalPrompt;

  // Combine all user messages into a comprehensive instruction
  const consolidated =
    "Analyze this trace with the following requirements (consolidated from user conversation):\n\n" +
    userMessages
      .map((msg, i) => {
        if (i === 0) return `Initial request: ${msg}`;
        return `Refinement ${i}: ${msg}`;
      })
      .join("\n") +
    "\n\nCombine all the above into a single comprehensive analysis.";

  return consolidated;
}

/**
 * Process widgets before saving — consolidate dynamicAnalysis prompts
 * using the conversation history.
 *
 * @param {Array} widgets - Current widget configs from the store
 * @param {Array} messages - Falcon conversation messages
 * @returns {Array} - Widgets with consolidated analysis prompts
 */
export function consolidateAnalysisPrompts(widgets, messages) {
  if (!widgets?.length) return widgets;

  const userMessages = getUserMessages(messages);

  // If no multi-turn conversation, return as-is
  if (userMessages.length <= 2) return widgets;

  return widgets.map((widget) => {
    // Only consolidate dynamicAnalysis widgets
    if (!widget.dynamicAnalysis?.prompt) return widget;

    return {
      ...widget,
      dynamicAnalysis: {
        ...widget.dynamicAnalysis,
        prompt: buildConsolidatedPrompt(
          userMessages,
          widget.dynamicAnalysis.prompt,
        ),
        // Store original prompt for reference
        _originalPrompt: widget.dynamicAnalysis.prompt,
      },
    };
  });
}
