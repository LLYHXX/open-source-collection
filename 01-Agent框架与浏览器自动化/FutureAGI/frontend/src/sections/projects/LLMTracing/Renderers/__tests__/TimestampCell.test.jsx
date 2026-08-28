import { describe, it, expect } from "vitest";
import { render, screen } from "src/utils/test-utils";
import TimestampCell from "../TimestampCell";

describe("TimestampCell", () => {
  it("renders an absolute-formatted date for a valid value", () => {
    // The cell shows the absolute date (tooltip holds relative time)
    const date = new Date("2026-03-15T10:30:00Z").toISOString();
    render(<TimestampCell value={date} />);
    // Match "Mar 15, 2026" (month may appear padded or unpadded across locales)
    expect(screen.getByText(/Mar\s+15,\s+2026/)).toBeInTheDocument();
  });

  it("renders '-' for null value", () => {
    render(<TimestampCell value={null} />);
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("renders '-' for undefined value", () => {
    render(<TimestampCell value={undefined} />);
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  it("renders '-' for invalid date string", () => {
    render(<TimestampCell value="not-a-date" />);
    expect(screen.getByText("-")).toBeInTheDocument();
  });
});
