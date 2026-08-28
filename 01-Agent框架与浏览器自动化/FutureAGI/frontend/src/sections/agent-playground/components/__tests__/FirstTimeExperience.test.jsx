import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import FirstTimeExperience from "../FirstTimeExperience";
import { useAgentPlaygroundStore } from "../../store";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
const mockNavigate = vi.fn();
vi.mock("react-router", () => ({
  useNavigate: () => mockNavigate,
}));

const mockCreateDemoAgent = vi.fn();
let mockIsPending = false;

vi.mock("../../../../api/agent-playground/agent-playground", () => ({
  useCreateGraph: () => ({
    mutate: mockCreateDemoAgent,
    isPending: mockIsPending,
  }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const theme = createTheme();
function renderFTE() {
  return render(
    <ThemeProvider theme={theme}>
      <FirstTimeExperience />
    </ThemeProvider>,
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("FirstTimeExperience", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAgentPlaygroundStore.getState().reset();
    mockIsPending = false;
  });

  it("renders start creating button", () => {
    renderFTE();

    expect(
      screen.getByRole("button", { name: /start creating/i }),
    ).toBeInTheDocument();
  });

  it("renders title text", () => {
    renderFTE();
    expect(screen.getByText("Agent Playground")).toBeInTheDocument();
  });

  it("handleStartCreating calls createDemoAgent without payload", () => {
    renderFTE();

    fireEvent.click(screen.getByRole("button", { name: /start creating/i }));

    expect(mockCreateDemoAgent).toHaveBeenCalledWith();
  });
});
