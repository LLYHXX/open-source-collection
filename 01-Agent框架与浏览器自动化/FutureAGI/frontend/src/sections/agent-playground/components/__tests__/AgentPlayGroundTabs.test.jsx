import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import AgentPlayGroundTabs from "../AgentPlayGroundTabs";
import { useAgentPlaygroundStore, useWorkflowRunStore } from "../../store";
import { AGENT_PLAYGROUND_TABS } from "../../utils/constants";
import { ThemeProvider, createTheme } from "@mui/material/styles";

// Mock SvgColor
vi.mock("src/components/svg-color", () => ({
  default: () => <span data-testid="svg-icon" />,
}));

// Mock Iconify
vi.mock("src/components/iconify", () => ({
  default: () => <span data-testid="iconify-icon" />,
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const theme = createTheme();

function renderWithRouter(initialPath = "/agents/123/build") {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[initialPath]}>
        <AgentPlayGroundTabs />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("AgentPlayGroundTabs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAgentPlaygroundStore.getState().reset();
    useWorkflowRunStore.getState().reset();
  });

  it("renders all tabs", () => {
    renderWithRouter();
    AGENT_PLAYGROUND_TABS.forEach((tab) => {
      expect(screen.getByText(tab.title || tab.label)).toBeInTheDocument();
    });
  });

  it("highlights current tab from URL path", () => {
    renderWithRouter("/agents/123/build");
    const buildTab = screen.getByRole("tab", { name: /Agent Builder/i });
    expect(buildTab).toHaveAttribute("aria-selected", "true");
  });

  it("navigates with ?version= from store's currentAgent.versionId", () => {
    useAgentPlaygroundStore.setState({
      currentAgent: { version_id: "v-42" },
    });
    renderWithRouter("/agents/123/build");

    // Click the Changelog tab
    const changelogTab = screen.getByRole("tab", { name: /Changelog/i });
    fireEvent.click(changelogTab);

    expect(mockNavigate).toHaveBeenCalledWith("changelog?version=v-42", {
      replace: true,
    });
  });

  it("no version param when versionId is absent", () => {
    useAgentPlaygroundStore.setState({
      currentAgent: { versionId: null },
    });
    renderWithRouter("/agents/123/build");

    const changelogTab = screen.getByRole("tab", { name: /Changelog/i });
    fireEvent.click(changelogTab);

    expect(mockNavigate).toHaveBeenCalledWith("changelog", { replace: true });
  });
});
