export function extractTextFromPrompt(prompt) {
  if (!Array.isArray(prompt)) {
    return "";
  }
  const texts = prompt.map((item) => {
    if (item.type === "text") {
      return item.text.trim();
    }
    return "";
  });
  return texts.join(" ");
}
