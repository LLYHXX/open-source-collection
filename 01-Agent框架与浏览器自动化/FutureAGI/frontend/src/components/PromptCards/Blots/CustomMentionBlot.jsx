import { MentionBlot as QuillMentionBlot } from "quill-mention";

export class CustomMentionBlot extends QuillMentionBlot {
  static create(data) {
    const node = super.create(data);
    node.setAttribute("data-id", data.id);
    node.setAttribute("data-value", data.value);
    node.setAttribute("data-denotation-char", data.denotationChar);
    node.setAttribute("data-valid", data.isValid ? "true" : "false");
    node.innerText = `{{${data.value}}}`;
    node.style.background = "none";
    node.style.padding = "0";

    node.style.color = data.isValid
      ? "var(--mention-valid-color)"
      : "var(--mention-invalid-color)";

    return node;
  }

  static value(node) {
    return {
      id: node.getAttribute("data-id"),
      value: node.getAttribute("data-value"),
      denotationChar: node.getAttribute("data-denotation-char"),
      isValid: node.getAttribute("data-valid") === "true",
    };
  }
}
