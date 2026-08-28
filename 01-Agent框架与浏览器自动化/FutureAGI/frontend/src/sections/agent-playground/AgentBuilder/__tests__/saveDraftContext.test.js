import { createElement } from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useSaveDraftContext } from "../saveDraftContext";
import SaveDraftContext from "../saveDraftContext";
import logger from "src/utils/logger";

// Mocks
vi.mock("src/utils/logger", () => ({
  default: { warn: vi.fn(), error: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
});

// Tests
describe("useSaveDraftContext", () => {
  describe("outside provider (fallback)", () => {
    it("returns fallback when used outside any provider (no throw)", () => {
      const { result } = renderHook(() => useSaveDraftContext());

      expect(result.current).toBeDefined();
      expect(result.current.saveDraft).toBeTypeOf("function");
      expect(result.current.ensureDraft).toBeTypeOf("function");
      expect(result.current.promoteDraft).toBeTypeOf("function");
    });

    it("fallback ensureDraft returns false (blocks mutations)", async () => {
      const { result } = renderHook(() => useSaveDraftContext());

      const value = await result.current.ensureDraft();

      expect(value).toBe(false);
    });

    it("fallback ensureDraft calls logger.warn", async () => {
      const { result } = renderHook(() => useSaveDraftContext());

      await result.current.ensureDraft();

      expect(logger.warn).toHaveBeenCalledTimes(1);
      expect(logger.warn).toHaveBeenCalledWith(
        "[SaveDraftContext] ensureDraft called outside SaveDraftProvider — mutation blocked",
      );
    });

    it("fallback saveDraft is a no-op function (doesn't throw)", () => {
      const { result } = renderHook(() => useSaveDraftContext());

      expect(() => result.current.saveDraft()).not.toThrow();
    });

    it("fallback promoteDraft is a no-op function (doesn't throw)", () => {
      const { result } = renderHook(() => useSaveDraftContext());

      expect(() => result.current.promoteDraft()).not.toThrow();
    });
  });

  describe("inside provider", () => {
    it("returns provided context value when inside SaveDraftProvider", () => {
      const mockContext = {
        saveDraft: vi.fn(),
        ensureDraft: vi.fn().mockResolvedValue(true),
        promoteDraft: vi.fn(),
      };

      const wrapper = ({ children }) =>
        createElement(
          SaveDraftContext.Provider,
          { value: mockContext },
          children,
        );

      const { result } = renderHook(() => useSaveDraftContext(), { wrapper });

      expect(result.current).toBe(mockContext);
      expect(result.current.saveDraft).toBe(mockContext.saveDraft);
      expect(result.current.ensureDraft).toBe(mockContext.ensureDraft);
      expect(result.current.promoteDraft).toBe(mockContext.promoteDraft);
    });
  });
});
