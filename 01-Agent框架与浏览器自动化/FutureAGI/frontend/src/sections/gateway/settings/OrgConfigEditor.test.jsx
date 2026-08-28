import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "src/utils/test-utils";
import userEvent from "@testing-library/user-event";
import OrgConfigEditor from "./OrgConfigEditor";

vi.mock("./ProviderConfigTab", () => ({
  default: () => <div>Providers tab</div>,
}));

vi.mock("./GuardrailConfigTab", () => ({
  default: () => <div>Guardrails tab</div>,
}));

vi.mock("./RoutingConfigTab", () => ({
  default: () => <div>Routing tab</div>,
}));

vi.mock("./CacheConfigTab", () => ({
  default: () => <div>Cache tab</div>,
}));

vi.mock("./RateLimitingConfigTab", () => ({
  default: () => <div>Rate limiting tab</div>,
}));

vi.mock("./BudgetsConfigTab", () => ({
  default: () => <div>Budgets tab</div>,
}));

vi.mock("./SecurityConfigTab", () => ({
  default: () => <div>Security tab</div>,
}));

vi.mock("./MCPConfigTab", () => ({
  default: () => <div>MCP tab</div>,
}));

vi.mock("./A2AConfigTab", () => ({
  default: () => <div>A2A tab</div>,
}));

vi.mock("./AuditConfigTab", () => ({
  default: () => <div>Audit tab</div>,
}));

vi.mock("./ModelDatabaseConfigTab", () => ({
  default: () => <div>Model database tab</div>,
}));

vi.mock("./ModelMapConfigTab", () => ({
  default: () => <div>Model map tab</div>,
}));

describe("OrgConfigEditor", () => {
  it("preserves alerting draft state when initialConfig changes after enabling alerting", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    const onSave = vi.fn();

    const initialConfig = {
      providers: {},
      alerting: {},
    };

    const { rerender } = render(
      <OrgConfigEditor
        open
        onClose={onClose}
        onSave={onSave}
        initialConfig={initialConfig}
        isSaving={false}
        defaultTab={7}
      />,
    );

    const alertingToggle = screen.getByRole("checkbox", {
      name: /enable per-org alerting/i,
    });

    expect(alertingToggle).not.toBeChecked();

    await user.click(alertingToggle);

    expect(alertingToggle).toBeChecked();
    expect(screen.getByText("Notification Channels")).toBeInTheDocument();

    rerender(
      <OrgConfigEditor
        open
        onClose={onClose}
        onSave={onSave}
        initialConfig={{
          ...initialConfig,
          _refetchVersion: 1,
        }}
        isSaving={false}
        defaultTab={7}
      />,
    );

    expect(
      screen.getByRole("checkbox", { name: /enable per-org alerting/i }),
    ).toBeChecked();
    expect(screen.getByText("Notification Channels")).toBeInTheDocument();
  });
});
