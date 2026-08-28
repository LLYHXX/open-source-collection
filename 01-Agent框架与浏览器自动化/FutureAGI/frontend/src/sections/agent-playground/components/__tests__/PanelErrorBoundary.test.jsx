import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PanelErrorBoundary from "../PanelErrorBoundary";
import logger from "src/utils/logger";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("src/utils/logger", () => ({
  default: { error: vi.fn(), warn: vi.fn() },
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
let shouldThrow = false;

function ThrowingChild() {
  if (shouldThrow) {
    throw new Error("Test render error");
  }
  return <div>Child content</div>;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("PanelErrorBoundary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    shouldThrow = false;
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("renders children normally when no error occurs", () => {
    render(
      <PanelErrorBoundary>
        <ThrowingChild />
      </PanelErrorBoundary>,
    );

    expect(screen.getByText("Child content")).toBeInTheDocument();
  });

  it("shows fallback UI when child throws", () => {
    shouldThrow = true;

    render(
      <PanelErrorBoundary>
        <ThrowingChild />
      </PanelErrorBoundary>,
    );

    expect(
      screen.getByText("Something went wrong while rendering this panel."),
    ).toBeInTheDocument();
  });

  it('shows "Retry" button in fallback UI', () => {
    shouldThrow = true;

    render(
      <PanelErrorBoundary>
        <ThrowingChild />
      </PanelErrorBoundary>,
    );

    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("clicking Retry re-renders children after error is fixed", () => {
    shouldThrow = true;

    render(
      <PanelErrorBoundary>
        <ThrowingChild />
      </PanelErrorBoundary>,
    );

    expect(
      screen.getByText("Something went wrong while rendering this panel."),
    ).toBeInTheDocument();

    // Fix the error before retrying
    shouldThrow = false;

    fireEvent.click(screen.getByRole("button", { name: /retry/i }));

    expect(screen.getByText("Child content")).toBeInTheDocument();
    expect(
      screen.queryByText("Something went wrong while rendering this panel."),
    ).not.toBeInTheDocument();
  });

  it("calls onRetry callback when retry is clicked", () => {
    shouldThrow = true;
    const onRetry = vi.fn();

    render(
      <PanelErrorBoundary onRetry={onRetry}>
        <ThrowingChild />
      </PanelErrorBoundary>,
    );

    shouldThrow = false;

    fireEvent.click(screen.getByRole("button", { name: /retry/i }));

    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("logs error via logger.error with the name prop as context", () => {
    shouldThrow = true;

    render(
      <PanelErrorBoundary name="TestPanel">
        <ThrowingChild />
      </PanelErrorBoundary>,
    );

    expect(logger.error).toHaveBeenCalledTimes(1);
    expect(logger.error.mock.calls[0][0]).toBe(
      "[TestPanel] Rendering error caught",
    );
  });

  it('uses default name "PanelErrorBoundary" when name prop is not provided', () => {
    shouldThrow = true;

    render(
      <PanelErrorBoundary>
        <ThrowingChild />
      </PanelErrorBoundary>,
    );

    expect(logger.error).toHaveBeenCalledTimes(1);
    expect(logger.error.mock.calls[0][0]).toBe(
      "[PanelErrorBoundary] Rendering error caught",
    );
  });
});
