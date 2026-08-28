import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import EditablePortLabel from "../EditablePortLabel";
import { useAgentPlaygroundStore } from "../../../store";

// ---- Mocks ----
const mockSaveDraft = vi.fn();
vi.mock("../../saveDraftContext", () => ({
  useSaveDraftContext: () => ({ saveDraft: mockSaveDraft }),
}));

vi.mock("notistack", () => ({
  enqueueSnackbar: vi.fn(),
}));

vi.mock("src/components/tooltip/CustomTooltip", () => ({
  default: ({ children }) => <>{children}</>,
}));

// ---- Helpers ----
const theme = createTheme();
const mockRenamePortDisplayName = vi.fn();

const makePort = (overrides = {}) => ({
  id: "port-1",
  display_name: "response",
  key: "response",
  direction: "output",
  ...overrides,
});

function renderLabel(props = {}) {
  const defaultProps = {
    nodeId: "node-1",
    port: makePort(),
    sx: {},
    ...props,
  };
  return render(
    <ThemeProvider theme={theme}>
      <EditablePortLabel {...defaultProps} />
    </ThemeProvider>,
  );
}

// ---- Tests ----
describe("EditablePortLabel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAgentPlaygroundStore.getState().reset();
    // Provide the mock since renamePortDisplayName is not in the store yet
    useAgentPlaygroundStore.setState({
      renamePortDisplayName: mockRenamePortDisplayName,
    });
  });

  it("renders display_name in view mode", () => {
    renderLabel();
    expect(screen.getByText("response")).toBeInTheDocument();
  });

  it("switches to edit mode on click", () => {
    renderLabel();
    fireEvent.click(screen.getByText("response"));
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveValue("response");
  });

  it("reverts on Escape", () => {
    renderLabel();
    fireEvent.click(screen.getByText("response"));

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "new_name" } });
    fireEvent.keyDown(input, { key: "Escape" });

    // Back to view mode with original name
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.getByText("response")).toBeInTheDocument();
  });

  it("calls renamePortDisplayName and saveDraft on Enter with new name", () => {
    renderLabel();
    fireEvent.click(screen.getByText("response"));

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "output_text" } });
    fireEvent.keyDown(input, { key: "Enter" });

    // renamePortDisplayName called with correct args
    expect(mockRenamePortDisplayName).toHaveBeenCalledWith(
      "node-1",
      "port-1",
      "output_text",
    );

    // saveDraft should be called
    expect(mockSaveDraft).toHaveBeenCalledTimes(1);
    expect(mockSaveDraft).toHaveBeenCalledWith(
      expect.objectContaining({ onError: expect.any(Function) }),
    );
  });

  it("does not save when name is unchanged", () => {
    renderLabel();
    fireEvent.click(screen.getByText("response"));

    const input = screen.getByRole("textbox");
    fireEvent.keyDown(input, { key: "Enter" });

    expect(mockSaveDraft).not.toHaveBeenCalled();
    expect(mockRenamePortDisplayName).not.toHaveBeenCalled();
  });

  it("does not save when name is empty", () => {
    renderLabel();
    fireEvent.click(screen.getByText("response"));

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(mockSaveDraft).not.toHaveBeenCalled();
    expect(mockRenamePortDisplayName).not.toHaveBeenCalled();
  });

  it("reverts on blur", () => {
    renderLabel();
    fireEvent.click(screen.getByText("response"));

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "changed" } });
    fireEvent.blur(input);

    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.getByText("response")).toBeInTheDocument();
    expect(mockSaveDraft).not.toHaveBeenCalled();
  });

  it("rolls back on saveDraft error", () => {
    renderLabel();
    fireEvent.click(screen.getByText("response"));

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "new_name" } });
    fireEvent.keyDown(input, { key: "Enter" });

    // Optimistic rename was called
    expect(mockRenamePortDisplayName).toHaveBeenCalledWith(
      "node-1",
      "port-1",
      "new_name",
    );

    // Simulate error callback — should call rename with old name to rollback
    const { onError } = mockSaveDraft.mock.calls[0][0];
    onError();

    expect(mockRenamePortDisplayName).toHaveBeenCalledWith(
      "node-1",
      "port-1",
      "response",
    );
  });
});
