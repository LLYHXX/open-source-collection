import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useDraftConfirmation } from "../useDraftConfirmation";
import { useAgentPlaygroundStore } from "../../store";

// ---------------------------------------------------------------------------
// useDraftConfirmation
// ---------------------------------------------------------------------------
describe("useDraftConfirmation", () => {
  beforeEach(() => {
    useAgentPlaygroundStore.getState().reset();
  });

  describe("isDraft", () => {
    it("true when currentAgent is null", () => {
      useAgentPlaygroundStore.setState({ currentAgent: null });
      const { result } = renderHook(() => useDraftConfirmation());
      expect(result.current.isDraft).toBe(true);
    });

    it("true when isDraft flag is true", () => {
      useAgentPlaygroundStore.setState({
        currentAgent: { id: "a1", is_draft: true, version_id: "v1" },
      });
      const { result } = renderHook(() => useDraftConfirmation());
      expect(result.current.isDraft).toBe(true);
    });

    it("true when no version_id", () => {
      useAgentPlaygroundStore.setState({
        currentAgent: { id: "a1", is_draft: false },
      });
      const { result } = renderHook(() => useDraftConfirmation());
      expect(result.current.isDraft).toBe(true);
    });

    it("false when active agent with versionId", () => {
      useAgentPlaygroundStore.setState({
        currentAgent: { id: "a1", is_draft: false, version_id: "v1" },
      });
      const { result } = renderHook(() => useDraftConfirmation());
      expect(result.current.isDraft).toBe(false);
    });
  });

  describe("confirmIfDraft", () => {
    it("calls callback directly when not a draft", () => {
      useAgentPlaygroundStore.setState({
        currentAgent: { id: "a1", is_draft: false, version_id: "v1" },
      });
      const { result } = renderHook(() => useDraftConfirmation());
      const callback = vi.fn();
      result.current.confirmIfDraft(callback);
      expect(callback).toHaveBeenCalledOnce();
    });

    it("opens dialog when draft", () => {
      useAgentPlaygroundStore.setState({ currentAgent: null });
      const { result } = renderHook(() => useDraftConfirmation());
      const callback = vi.fn();
      result.current.confirmIfDraft(callback, "Custom message");
      // Callback should NOT be called directly
      expect(callback).not.toHaveBeenCalled();
      // Dialog should be open with callback stored
      const dialog = useAgentPlaygroundStore.getState().draftConfirmDialog;
      expect(dialog.open).toBe(true);
      expect(dialog.callback).toBe(callback);
      expect(dialog.message).toBe("Custom message");
    });
  });
});
