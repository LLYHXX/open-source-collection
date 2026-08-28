import PropTypes from "prop-types";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "src/utils/test-utils";
import QuickActions from "../components/QuickActions";

// Mock Iconify
function MockIconify({ icon, ...props }) {
  return <span data-testid="iconify" data-icon={icon} {...props} />;
}

MockIconify.propTypes = {
  icon: PropTypes.string.isRequired,
};

vi.mock("src/components/iconify", () => ({
  default: MockIconify,
}));

describe("QuickActions", () => {
  it("renders 5 quick action chips", () => {
    render(<QuickActions onAction={vi.fn()} />);
    const chips = screen.getAllByRole("button");
    expect(chips).toHaveLength(5);
  });

  it("renders expected action labels", () => {
    render(<QuickActions onAction={vi.fn()} />);
    expect(screen.getByText("Analyse my error feed")).toBeInTheDocument();
    expect(screen.getByText("Build a dataset")).toBeInTheDocument();
    expect(screen.getByText("Create an evaluation")).toBeInTheDocument();
    expect(screen.getByText("Create an Imagine view")).toBeInTheDocument();
    expect(screen.getByText("Run simulation for my agent")).toBeInTheDocument();
  });

  it("calls onAction with the chip's full prompt when clicked", () => {
    const onAction = vi.fn();
    render(<QuickActions onAction={onAction} />);
    fireEvent.click(screen.getByText("Build a dataset"));
    expect(onAction).toHaveBeenCalledTimes(1);
    const sent = onAction.mock.calls[0][0];
    expect(sent).toMatch(/Build a dataset from my traces/i);
    expect(sent.length).toBeGreaterThan(80);
  });

  it("handles missing onAction prop gracefully", () => {
    render(<QuickActions />);
    // Clicking should not throw
    expect(() => {
      fireEvent.click(screen.getByText("Build a dataset"));
    }).not.toThrow();
  });
});
