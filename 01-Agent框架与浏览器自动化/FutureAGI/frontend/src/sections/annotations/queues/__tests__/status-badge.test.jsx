import { describe, it, expect } from "vitest";
import { render, screen } from "src/utils/test-utils";
import StatusBadge from "../components/status-badge";

describe("StatusBadge", () => {
  it("renders Draft status", () => {
    render(<StatusBadge status="draft" />);
    expect(screen.getByText("Draft")).toBeInTheDocument();
  });

  it("renders Active status", () => {
    render(<StatusBadge status="active" />);
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("renders Paused status", () => {
    render(<StatusBadge status="paused" />);
    expect(screen.getByText("Paused")).toBeInTheDocument();
  });

  it("renders Completed status", () => {
    render(<StatusBadge status="completed" />);
    expect(screen.getByText("Completed")).toBeInTheDocument();
  });

  it("falls back to Draft for unknown status", () => {
    render(<StatusBadge status="unknown" />);
    expect(screen.getByText("Draft")).toBeInTheDocument();
  });
});
