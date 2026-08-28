import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useModelParameters } from "../useModelParameters";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------
const makeSlider = (label, value = 0.5, overrides = {}) => ({
  label,
  value,
  default: value,
  min: 0,
  max: 1,
  step: 0.1,
  ...overrides,
});

const makeBoolean = (label, value = false, overrides = {}) => ({
  label,
  value,
  default: value,
  ...overrides,
});

const makeDropdown = (label, options = ["a", "b"], overrides = {}) => ({
  label,
  options,
  value: options[0],
  default: options[0],
  ...overrides,
});

const baseModelParams = {
  sliders: [makeSlider("Temperature"), makeSlider("Top P", 0.9)],
  booleans: [makeBoolean("Stream")],
  dropdowns: [makeDropdown("Response Format")],
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("useModelParameters", () => {
  beforeEach(() => {
    // noop — each test renders its own hook
  });

  // ---- Initial state ----
  it("returns initial empty state when watchedModel is null", () => {
    const { result } = renderHook(() => useModelParameters(null, null, null));

    expect(result.current.modelParameters).toEqual({
      sliders: [],
      dropdowns: [],
      booleans: [],
      reasoning: { sliders: [], dropdowns: [], showReasoningProcess: true },
    });
  });

  // ---- Parameter initialization from API ----
  it("initializes parameters from modelParams", () => {
    const { result } = renderHook(() =>
      useModelParameters(baseModelParams, "gpt-4", null),
    );

    expect(result.current.modelParameters.sliders).toHaveLength(2);
    expect(result.current.modelParameters.sliders[0].id).toBe("temperature");
    expect(result.current.modelParameters.sliders[0].value).toBe(0.5);
    expect(result.current.modelParameters.booleans).toHaveLength(1);
    expect(result.current.modelParameters.dropdowns).toHaveLength(1);
  });

  // ---- Saved config applied once per model ----
  it("applies saved configuration on first load", () => {
    const savedConfig = {
      Temperature: 0.8,
      "Top P": 0.7,
      booleans: { Stream: true },
      dropdowns: { "Response Format": "b" },
    };

    const { result } = renderHook(() =>
      useModelParameters(baseModelParams, "gpt-4", savedConfig),
    );

    expect(result.current.modelParameters.sliders[0].value).toBe(0.8);
    expect(result.current.modelParameters.sliders[1].value).toBe(0.7);
    expect(result.current.modelParameters.booleans[0].value).toBe(true);
    expect(result.current.modelParameters.dropdowns[0].value).toBe("b");
  });

  it("does not re-apply saved config after first load for same model", () => {
    const savedConfig = { Temperature: 0.8 };

    const { result, rerender } = renderHook(
      ({ model }) => useModelParameters(baseModelParams, model, savedConfig),
      { initialProps: { model: "gpt-4" } },
    );

    // First render applies saved config
    expect(result.current.modelParameters.sliders[0].value).toBe(0.8);

    // User changes value
    act(() => result.current.updateSliderParameter(0, 0.3));
    expect(result.current.modelParameters.sliders[0].value).toBe(0.3);

    // Re-render with same model — should NOT re-apply saved config
    rerender({ model: "gpt-4" });
    expect(result.current.modelParameters.sliders[0].value).toBe(0.3);
  });

  // ---- Model change resets ----
  it("resets parameters when model changes", () => {
    const { result, rerender } = renderHook(
      ({ model, params }) => useModelParameters(params, model, null),
      { initialProps: { model: "gpt-4", params: baseModelParams } },
    );

    expect(result.current.modelParameters.sliders).toHaveLength(2);

    const newParams = {
      sliders: [makeSlider("Temperature", 0.7)],
      booleans: [],
      dropdowns: [],
    };

    rerender({ model: "claude-3", params: newParams });

    expect(result.current.modelParameters.sliders).toHaveLength(1);
    expect(result.current.modelParameters.sliders[0].value).toBe(0.7);
  });

  it("resets to initial state when watchedModel becomes null", () => {
    const { result, rerender } = renderHook(
      ({ model }) => useModelParameters(baseModelParams, model, null),
      { initialProps: { model: "gpt-4" } },
    );

    expect(result.current.modelParameters.sliders).toHaveLength(2);

    rerender({ model: null });

    expect(result.current.modelParameters.sliders).toHaveLength(0);
  });

  // ---- Update functions ----
  it("updateSliderParameter updates value at index", () => {
    const { result } = renderHook(() =>
      useModelParameters(baseModelParams, "gpt-4", null),
    );

    act(() => result.current.updateSliderParameter(0, 0.99));

    expect(result.current.modelParameters.sliders[0].value).toBe(0.99);
    expect(result.current.modelParameters.sliders[1].value).toBe(0.9); // unchanged
  });

  it("updateBooleanParameter updates value at index", () => {
    const { result } = renderHook(() =>
      useModelParameters(baseModelParams, "gpt-4", null),
    );

    act(() => result.current.updateBooleanParameter(0, true));

    expect(result.current.modelParameters.booleans[0].value).toBe(true);
  });

  it("updateDropdownParameter updates value at index", () => {
    const { result } = renderHook(() =>
      useModelParameters(baseModelParams, "gpt-4", null),
    );

    act(() => result.current.updateDropdownParameter(0, "b"));

    expect(result.current.modelParameters.dropdowns[0].value).toBe("b");
  });

  // ---- Reasoning parameters ----
  it("initializes reasoning parameters when present", () => {
    const paramsWithReasoning = {
      ...baseModelParams,
      reasoning: {
        sliders: [makeSlider("Budget Tokens", 1000, { min: 0, max: 5000 })],
        dropdowns: [makeDropdown("Reasoning Mode", ["standard", "extended"])],
      },
    };

    const { result } = renderHook(() =>
      useModelParameters(paramsWithReasoning, "o1", null),
    );

    expect(result.current.modelParameters.reasoning.sliders).toHaveLength(1);
    expect(result.current.modelParameters.reasoning.dropdowns).toHaveLength(1);
    expect(result.current.modelParameters.reasoning.sliders[0].id).toBe(
      "budgetTokens",
    );
  });

  it("clears reasoning when model does not support it", () => {
    const paramsWithoutReasoning = {
      sliders: [makeSlider("Temperature")],
      booleans: [],
      dropdowns: [],
      // no reasoning key
    };

    const { result } = renderHook(() =>
      useModelParameters(paramsWithoutReasoning, "gpt-4", null),
    );

    expect(result.current.modelParameters.reasoning).toBeNull();
  });

  it("updateReasoningSliderParameter updates reasoning slider", () => {
    const paramsWithReasoning = {
      ...baseModelParams,
      reasoning: {
        sliders: [makeSlider("Budget Tokens", 1000)],
        dropdowns: [],
      },
    };

    const { result } = renderHook(() =>
      useModelParameters(paramsWithReasoning, "o1", null),
    );

    act(() => result.current.updateReasoningSliderParameter(0, 2000));

    expect(result.current.modelParameters.reasoning.sliders[0].value).toBe(
      2000,
    );
  });

  it("updateReasoningDropdownParameter updates reasoning dropdown", () => {
    const paramsWithReasoning = {
      ...baseModelParams,
      reasoning: {
        sliders: [],
        dropdowns: [makeDropdown("Reasoning Mode", ["standard", "extended"])],
      },
    };

    const { result } = renderHook(() =>
      useModelParameters(paramsWithReasoning, "o1", null),
    );

    act(() => result.current.updateReasoningDropdownParameter(0, "extended"));

    expect(result.current.modelParameters.reasoning.dropdowns[0].value).toBe(
      "extended",
    );
  });

  it("updateShowReasoningProcess updates the flag", () => {
    const paramsWithReasoning = {
      ...baseModelParams,
      reasoning: { sliders: [], dropdowns: [] },
    };

    const { result } = renderHook(() =>
      useModelParameters(paramsWithReasoning, "o1", null),
    );

    act(() => result.current.updateShowReasoningProcess(false));

    expect(result.current.modelParameters.reasoning.showReasoningProcess).toBe(
      false,
    );
  });

  // ---- Parameter ID deduplication ----
  it("deduplicates parameters by ID", () => {
    const { result, rerender } = renderHook(
      ({ params }) => useModelParameters(params, "gpt-4", null),
      { initialProps: { params: baseModelParams } },
    );

    expect(result.current.modelParameters.sliders).toHaveLength(2);

    // Re-render with same params — should not add duplicates
    rerender({ params: baseModelParams });

    expect(result.current.modelParameters.sliders).toHaveLength(2);
  });

  // ---- No modelParams with model present ----
  it("resets to initial when modelParams is null but model exists", () => {
    const { result, rerender } = renderHook(
      ({ params, model }) => useModelParameters(params, model, null),
      { initialProps: { params: baseModelParams, model: "gpt-4" } },
    );

    expect(result.current.modelParameters.sliders).toHaveLength(2);

    rerender({ params: null, model: "claude-3" });

    expect(result.current.modelParameters.sliders).toHaveLength(0);
  });

  // ---- Saved config applied via camelCase id ----
  it("applies saved config by camelCase id when label key missing", () => {
    const savedConfig = {
      topP: 0.6, // id-based key instead of "Top P"
    };

    const { result } = renderHook(() =>
      useModelParameters(baseModelParams, "gpt-4", savedConfig),
    );

    expect(result.current.modelParameters.sliders[1].value).toBe(0.6);
  });
});

// ---------------------------------------------------------------------------
// Edge cases
// ---------------------------------------------------------------------------
describe("useModelParameters – edge cases", () => {
  // ---- Falsy-but-valid saved values ----
  it("preserves saved Temperature=0 instead of falling through to defaults", () => {
    const params = {
      sliders: [makeSlider("Temperature", 0.7)],
      booleans: [],
      dropdowns: [],
    };
    const savedConfig = { Temperature: 0 };

    const { result } = renderHook(() =>
      useModelParameters(params, "gpt-4", savedConfig),
    );

    // `??` does NOT treat 0 as nullish, so the saved value must be kept
    expect(result.current.modelParameters.sliders[0].value).toBe(0);
  });

  it("preserves saved boolean false instead of falling through to defaults", () => {
    const params = {
      sliders: [],
      booleans: [makeBoolean("Stream", true)],
      dropdowns: [],
    };
    const savedConfig = { booleans: { Stream: false } };

    const { result } = renderHook(() =>
      useModelParameters(params, "gpt-4", savedConfig),
    );

    // `??` does NOT treat false as nullish, so the saved value must be kept
    expect(result.current.modelParameters.booleans[0].value).toBe(false);
  });

  // ---- updateSliderParameter with out-of-bounds index ----
  it("updateSliderParameter with out-of-bounds index is a no-op", () => {
    const { result } = renderHook(() =>
      useModelParameters(baseModelParams, "gpt-4", null),
    );

    const slidersBefore = result.current.modelParameters.sliders.map(
      (s) => s.value,
    );

    act(() => result.current.updateSliderParameter(999, 0.42));

    const slidersAfter = result.current.modelParameters.sliders.map(
      (s) => s.value,
    );

    expect(slidersAfter).toEqual(slidersBefore);
  });

  // ---- savedConfiguration is undefined ----
  it("uses parameter defaults when savedConfiguration is undefined", () => {
    const params = {
      sliders: [makeSlider("Temperature", 0.5)],
      booleans: [makeBoolean("Stream", false)],
      dropdowns: [makeDropdown("Response Format", ["json", "text"])],
    };

    const { result } = renderHook(() =>
      useModelParameters(params, "gpt-4", undefined),
    );

    expect(result.current.modelParameters.sliders[0].value).toBe(0.5);
    expect(result.current.modelParameters.booleans[0].value).toBe(false);
    expect(result.current.modelParameters.dropdowns[0].value).toBe("json");
  });
});
