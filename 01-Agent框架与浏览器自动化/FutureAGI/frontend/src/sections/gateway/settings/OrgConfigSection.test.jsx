import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "src/utils/test-utils";
import OrgConfigSection from "./OrgConfigSection";

const mockMutate = vi.fn();

let mockOrgConfigReturn = {
  data: null,
  isLoading: false,
  error: null,
};

let mockProviderHealthReturn = {
  data: { providers: [] },
};

vi.mock("../providers/hooks/useOrgConfig", () => ({
  useOrgConfig: () => mockOrgConfigReturn,
  useCreateOrgConfig: () => ({ mutate: mockMutate, isPending: false }),
}));

vi.mock("../providers/hooks/useGatewayConfig", () => ({
  useProviderHealth: () => mockProviderHealthReturn,
}));

vi.mock("../context/useGatewayContext", () => ({
  useGatewayContext: () => ({ gatewayId: "gateway-1" }),
}));

vi.mock("./OrgConfigEditor", () => ({
  default: () => <div>Org config editor</div>,
}));

vi.mock("./ConfigHistoryDrawer", () => ({
  default: () => <div>Config history drawer</div>,
}));

describe("OrgConfigSection", () => {
  beforeEach(() => {
    mockMutate.mockReset();
    mockOrgConfigReturn = {
      data: null,
      isLoading: false,
      error: null,
    };
    mockProviderHealthReturn = {
      data: { providers: [] },
    };
  });

  it("renders snake_case metadata and guardrail count from rules fallback", () => {
    const createdAt = "2026-04-14T08:34:37.245253Z";

    mockOrgConfigReturn = {
      data: {
        id: "cfg-1",
        version: 48,
        created_at: createdAt,
        change_description: "Update guardrail pii-detector",
        guardrails: {
          enabled: true,
          checks: {},
          rules: [
            { name: "pii-detector", stage: "pre", action: "block" },
            { name: "content-moderation", stage: "pre", action: "block" },
          ],
        },
        routing: { strategy: "fallback" },
        cache: { enabled: true, backend: "memory" },
      },
      isLoading: false,
      error: null,
    };

    mockProviderHealthReturn = {
      data: {
        providers: [{ name: "openai" }, { name: "anthropic" }],
      },
    };

    render(<OrgConfigSection />);

    expect(screen.getByText(/Last Updated:/)).toBeInTheDocument();
    expect(
      screen.getByText(/Update guardrail pii-detector/),
    ).toBeInTheDocument();
    expect(screen.getAllByText("2")).toHaveLength(2);
    expect(screen.getAllByText(/2 configured/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/2 overrides/i)[0]).toBeInTheDocument();
  });
});
