import { describe, it, expect, vi } from "vitest";
import { fireEvent } from "@testing-library/react";
import { render } from "src/utils/test-utils";
import VoiceDrawerHeader from "../VoiceDrawerHeader";

const renderHeader = (props = {}) =>
  render(
    <VoiceDrawerHeader
      callId="call-123"
      onClose={vi.fn()}
      onPrev={vi.fn()}
      onNext={vi.fn()}
      hasPrev
      hasNext
      {...props}
    />,
  );

describe("VoiceDrawerHeader keyboard nav", () => {
  it("ArrowDown calls onNext when hasNext", () => {
    const onNext = vi.fn();
    renderHeader({ onNext });
    fireEvent.keyDown(document, { key: "ArrowDown" });
    expect(onNext).toHaveBeenCalledTimes(1);
  });

  it("ArrowUp calls onPrev when hasPrev", () => {
    const onPrev = vi.fn();
    renderHeader({ onPrev });
    fireEvent.keyDown(document, { key: "ArrowUp" });
    expect(onPrev).toHaveBeenCalledTimes(1);
  });

  it("ArrowDown does nothing when hasNext is false", () => {
    const onNext = vi.fn();
    renderHeader({ onNext, hasNext: false });
    fireEvent.keyDown(document, { key: "ArrowDown" });
    expect(onNext).not.toHaveBeenCalled();
  });

  it("ArrowUp does nothing when hasPrev is false", () => {
    const onPrev = vi.fn();
    renderHeader({ onPrev, hasPrev: false });
    fireEvent.keyDown(document, { key: "ArrowUp" });
    expect(onPrev).not.toHaveBeenCalled();
  });

  it("ignores arrows when focus is on an INPUT", () => {
    const onNext = vi.fn();
    renderHeader({ onNext });
    const input = document.createElement("input");
    document.body.appendChild(input);
    try {
      input.focus();
      fireEvent.keyDown(input, { key: "ArrowDown" });
      expect(onNext).not.toHaveBeenCalled();
    } finally {
      document.body.removeChild(input);
    }
  });
});
