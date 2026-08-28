import PropTypes from "prop-types";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "src/utils/test-utils";
import ThoughtsSection from "../components/ThoughtsSection";

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

const COMPLETED_THOUGHTS = [
  { step: 1, name: "list_datasets", status: "completed", result: "Found 3" },
  { step: 2, name: "search", status: "completed", result: "5 results" },
  { step: 3, name: "read_schema", status: "completed", result: "Done" },
];

const STREAMING_THOUGHTS = [
  { step: 1, name: "list_datasets", status: "completed", result: "Found 3" },
  { step: 2, name: "search", status: "in_progress", result: "" },
  { step: 3, name: "read_schema", status: "pending", result: "" },
];

describe("ThoughtsSection", () => {
  it("returns null when thoughts is empty", () => {
    const { container } = render(<ThoughtsSection thoughts={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("returns null when thoughts is null", () => {
    const { container } = render(<ThoughtsSection thoughts={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders header with completed status when all done", () => {
    render(<ThoughtsSection thoughts={COMPLETED_THOUGHTS} />);
    expect(screen.getByText("3 steps completed")).toBeInTheDocument();
  });

  it("renders header with thinking status when streaming", () => {
    render(<ThoughtsSection thoughts={STREAMING_THOUGHTS} isStreaming />);
    expect(screen.getByText(/Thinking/)).toBeInTheDocument();
  });

  it("auto-expands when streaming, shows steps", () => {
    render(<ThoughtsSection thoughts={STREAMING_THOUGHTS} isStreaming />);
    // Steps should be visible when streaming (auto-expanded)
    expect(screen.getByText("list_datasets")).toBeInTheDocument();
    expect(screen.getByText("search")).toBeInTheDocument();
  });

  it("shows result text for completed thoughts", () => {
    render(<ThoughtsSection thoughts={STREAMING_THOUGHTS} isStreaming />);
    expect(screen.getByText("Found 3")).toBeInTheDocument();
  });

  it("can toggle expanded state by clicking header", () => {
    render(<ThoughtsSection thoughts={COMPLETED_THOUGHTS} />);
    // Click to expand
    fireEvent.click(screen.getByText("3 steps completed"));
    expect(screen.getByText("list_datasets")).toBeVisible();
    expect(screen.getByText("Found 3")).toBeVisible();
  });

  it("renders single thought correctly", () => {
    const single = [
      { step: 1, name: "whoami", status: "completed", result: "Test User" },
    ];
    render(<ThoughtsSection thoughts={single} />);
    expect(screen.getByText("1 step completed")).toBeInTheDocument();
    fireEvent.click(screen.getByText("1 step completed"));
    expect(screen.getByText("whoami")).toBeInTheDocument();
    expect(screen.getByText("Test User")).toBeInTheDocument();
  });
});
