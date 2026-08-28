const OPEN_TAG = "<thinking>";
// <thinking> tags are injected by the backend (not the LLM API) to wrap
// model thinking content. Self-closing <thinking /> is a valid closing form.
const CLOSE_TAGS = ["</thinking>", "<thinking />"];

export function parseThinkingContent(text) {
  if (!text || typeof text !== "string") {
    return { thinking: null, content: text };
  }

  const startIdx = text.indexOf(OPEN_TAG);
  if (startIdx === -1) {
    return { thinking: null, content: text };
  }

  const afterOpen = startIdx + OPEN_TAG.length;

  // Find the earliest closing tag
  let endIdx = -1;
  let closeTagLen = 0;
  for (const tag of CLOSE_TAGS) {
    const idx = text.indexOf(tag, afterOpen);
    if (idx !== -1 && (endIdx === -1 || idx < endIdx)) {
      endIdx = idx;
      closeTagLen = tag.length;
    }
  }

  // No closing tag yet — still streaming thinking content
  if (endIdx === -1) {
    return {
      thinking: text.slice(afterOpen),
      content: "",
      isThinking: true,
    };
  }

  return {
    thinking: text.slice(afterOpen, endIdx),
    content: text.slice(endIdx + closeTagLen).trim(),
    isThinking: false,
  };
}
