/* eslint-disable react/prop-types */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { usePromptNodeQueries } from "../usePromptNodeQueries";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
let mockResponseSchemaData = null;
let mockModelParamsData = null;

vi.mock("src/utils/axios", () => ({
  default: {
    get: vi.fn((url) => {
      if (url?.includes?.("response-schema") || url === "/response-schema") {
        return Promise.resolve({
          data: { results: mockResponseSchemaData },
        });
      }
      if (url?.includes?.("model-params") || url === "/model-params") {
        return Promise.resolve({
          data: { result: mockModelParamsData },
        });
      }
      return Promise.resolve({ data: {} });
    }),
  },
  endpoints: {
    develop: {
      runPrompt: { responseSchema: "/response-schema" },
      modelParams: "/model-params",
    },
  },
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function createQueryWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0, gcTime: 0 },
    },
  });
  function QueryWrapper({ children }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  }
  return QueryWrapper;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("usePromptNodeQueries", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockResponseSchemaData = null;
    mockModelParamsData = null;
  });

  it("returns default response format menu items", () => {
    const wrapper = createQueryWrapper();
    const { result } = renderHook(() => usePromptNodeQueries(null, null), {
      wrapper,
    });

    // Before queries resolve, should have defaults
    expect(result.current.responseFormatMenuItems).toEqual([
      { value: "text", label: "Text" },
      { value: "json", label: "JSON" },
    ]);
  });

  it("returns modelParams and responseSchema as null initially", () => {
    const wrapper = createQueryWrapper();
    const { result } = renderHook(() => usePromptNodeQueries(null, null), {
      wrapper,
    });

    expect(result.current.modelParams).toBeUndefined();
    expect(result.current.responseSchema).toBeUndefined();
  });

  it("adds custom schemas to response format menu items", async () => {
    mockResponseSchemaData = [
      { id: "schema-1", name: "Custom Schema" },
      { id: "schema-2", name: "Another Schema" },
    ];

    const wrapper = createQueryWrapper();
    const { result } = renderHook(() => usePromptNodeQueries(null, null), {
      wrapper,
    });

    // Wait for query to resolve
    await waitFor(() => {
      expect(result.current.responseSchema).toBeDefined();
    });

    const items = result.current.responseFormatMenuItems;
    expect(items).toContainEqual({ label: "Custom Schema", value: "schema-1" });
    expect(items).toContainEqual({
      label: "Another Schema",
      value: "schema-2",
    });
  });

  it("adds model-specific formats with deduplication", async () => {
    mockResponseSchemaData = [];
    mockModelParamsData = {
      responseFormat: [
        { value: "text" }, // duplicate of default — should be skipped
        { value: "structured_output" }, // new — should be added
      ],
    };

    const wrapper = createQueryWrapper();
    const { result } = renderHook(
      () => usePromptNodeQueries("gpt-4", "openai"),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.modelParams).toBeDefined();
    });

    const items = result.current.responseFormatMenuItems;
    const textItems = items.filter((i) => i.value === "text");
    expect(textItems).toHaveLength(1); // not duplicated

    expect(items).toContainEqual({
      label: "Structured Output",
      value: "structured_output",
    });
  });

  it("does not fetch model params when model or provider is missing", () => {
    const wrapper = createQueryWrapper();
    const { result } = renderHook(() => usePromptNodeQueries(null, "openai"), {
      wrapper,
    });

    expect(result.current.modelParams).toBeUndefined();
  });
});
