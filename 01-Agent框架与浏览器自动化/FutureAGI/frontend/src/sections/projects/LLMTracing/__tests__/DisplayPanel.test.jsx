import { describe, it, expect, vi } from "vitest";
import { render, screen } from "src/utils/test-utils";
import DisplayPanel from "../DisplayPanel";

vi.mock("src/components/iconify", () => ({
  default: () => null,
}));

const baseProps = {
  anchorEl: document.createElement("button"),
  open: true,
  onClose: vi.fn(),
  mode: "traces",
  viewMode: "graph",
  cellHeight: "Short",
};

describe("DisplayPanel — Add custom columns badge (TH-4139)", () => {
  it("shows '2 added' when there are 2 unique custom columns", () => {
    const columns = [
      { id: "trace_name" },
      { id: "llm.token_count.prompt", groupBy: "Custom Columns" },
      {
        id: "gen_ai.output.messages.0.message.role",
        groupBy: "Custom Columns",
      },
    ];
    render(<DisplayPanel {...baseProps} columns={columns} />);
    expect(screen.getByText("2 added")).toBeInTheDocument();
  });

  it("dedupes by id so duplicate custom columns count once", () => {
    const columns = [
      { id: "trace_name" },
      { id: "llm.token_count.prompt", groupBy: "Custom Columns" },
      { id: "llm.token_count.prompt", groupBy: "Custom Columns" },
    ];
    render(<DisplayPanel {...baseProps} columns={columns} />);
    expect(screen.getByText("1 added")).toBeInTheDocument();
  });

  it("hides the badge when no custom columns are added", () => {
    const columns = [{ id: "trace_name" }, { id: "input" }];
    render(<DisplayPanel {...baseProps} columns={columns} />);
    expect(screen.queryByText(/added/)).not.toBeInTheDocument();
  });
});
