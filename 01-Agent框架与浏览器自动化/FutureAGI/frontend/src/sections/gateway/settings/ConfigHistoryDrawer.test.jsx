import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "src/utils/test-utils";
import userEvent from "@testing-library/user-event";
import ConfigHistoryDrawer from "./ConfigHistoryDrawer";

const mockActivate = vi.fn();

let mockHistoryReturn = {
  data: [],
  isLoading: false,
};

vi.mock("../providers/hooks/useOrgConfig", () => ({
  useOrgConfigHistory: () => mockHistoryReturn,
  useActivateOrgConfig: () => ({ mutate: mockActivate, isPending: false }),
}));

describe("ConfigHistoryDrawer", () => {
  beforeEach(() => {
    mockActivate.mockReset();
    mockHistoryReturn = {
      data: [],
      isLoading: false,
    };
  });

  it("renders snake_case history metadata and hides activate for active config", async () => {
    const user = userEvent.setup();
    const createdAt = "2026-04-14T08:34:37.245253Z";

    mockHistoryReturn = {
      data: [
        {
          id: "cfg-1",
          version: 48,
          is_active: true,
          created_at: createdAt,
          change_description: "Update guardrail pii-detector",
          guardrails: { rules: [] },
          routing: {},
          cache: {},
        },
      ],
      isLoading: false,
    };

    render(<ConfigHistoryDrawer open onClose={vi.fn()} />);

    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(
      screen.getByText(new Date(createdAt).toLocaleDateString()),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Update guardrail pii-detector"),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /activate/i }),
    ).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /view/i }));

    expect(screen.queryByText(/"providers"/)).not.toBeInTheDocument();
  });
});
