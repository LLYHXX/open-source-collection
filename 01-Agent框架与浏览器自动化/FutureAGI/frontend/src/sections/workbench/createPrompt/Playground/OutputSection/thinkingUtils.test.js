import { describe, it, expect } from "vitest";
import { parseThinkingContent } from "./thinkingUtils";

describe("parseThinkingContent", () => {
  it("returns null thinking for text without thinking tags", () => {
    const result = parseThinkingContent("Hello world");
    expect(result).toEqual({ thinking: null, content: "Hello world" });
  });

  it("returns null thinking for null/undefined input", () => {
    expect(parseThinkingContent(null)).toEqual({
      thinking: null,
      content: null,
    });
    expect(parseThinkingContent(undefined)).toEqual({
      thinking: null,
      content: undefined,
    });
    expect(parseThinkingContent("")).toEqual({ thinking: null, content: "" });
  });

  it("returns null thinking for non-string input", () => {
    expect(parseThinkingContent(123)).toEqual({ thinking: null, content: 123 });
  });

  it("extracts thinking from a complete block", () => {
    const text = "<thinking>some thought</thinking>actual content";
    const result = parseThinkingContent(text);
    expect(result).toEqual({
      thinking: "some thought",
      content: "actual content",
      isThinking: false,
    });
  });

  it("handles open tag only (streaming in progress)", () => {
    const text = "<thinking>partial thought still streaming";
    const result = parseThinkingContent(text);
    expect(result).toEqual({
      thinking: "partial thought still streaming",
      content: "",
      isThinking: true,
    });
  });

  it("handles self-closing <thinking /> tag", () => {
    const text = "<thinking>some thought<thinking />actual content";
    const result = parseThinkingContent(text);
    expect(result).toEqual({
      thinking: "some thought",
      content: "actual content",
      isThinking: false,
    });
  });

  it("handles empty thinking block", () => {
    const text = "<thinking></thinking>content after";
    const result = parseThinkingContent(text);
    expect(result).toEqual({
      thinking: "",
      content: "content after",
      isThinking: false,
    });
  });

  it("trims whitespace from content after closing tag", () => {
    const text = "<thinking>thought</thinking>   spaced content   ";
    const result = parseThinkingContent(text);
    expect(result).toEqual({
      thinking: "thought",
      content: "spaced content",
      isThinking: false,
    });
  });

  it("picks the earliest closing tag when both forms are present", () => {
    const text = "<thinking>thought</thinking>middle<thinking />end";
    const result = parseThinkingContent(text);
    expect(result).toEqual({
      thinking: "thought",
      content: "middle<thinking />end",
      isThinking: false,
    });
  });
});
