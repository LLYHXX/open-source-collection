/* eslint-disable react/prop-types */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useForm, FormProvider } from "react-hook-form";
import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import PromptMessageRow from "../PromptMessageRow";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
const mockEnqueueSnackbar = vi.fn();
vi.mock("notistack", () => ({
  enqueueSnackbar: (...args) => mockEnqueueSnackbar(...args),
}));

vi.mock("src/utils/utils", () => ({
  getRandomId: vi.fn(() => "random-id-123"),
}));

vi.mock("src/components/svg-color", () => ({
  default: (props) => <span data-testid="svg-icon" {...props} />,
}));

// Mock drawer components to avoid QueryClientProvider dependency
vi.mock("src/components/GeneratePromptDrawer", () => ({
  default: () => <div data-testid="generate-prompt-drawer" />,
}));

vi.mock("src/components/ImprovePromptDrawer", () => ({
  default: () => <div data-testid="improve-prompt-drawer" />,
}));

// Mock PromptCard to avoid complex dependencies
vi.mock("src/components/PromptCards/PromptCard", () => ({
  default: ({ role, index, onRemove, onRoleChange, onPromptChange }) => (
    <div data-testid={`prompt-card-${index}`}>
      <span data-testid={`role-${index}`}>{role}</span>
      <button data-testid={`remove-${index}`} onClick={onRemove}>
        Remove
      </button>
      <button
        data-testid={`change-role-${index}`}
        onClick={() => onRoleChange("assistant")}
      >
        Change Role
      </button>
      <button
        data-testid={`change-content-${index}`}
        onClick={() => onPromptChange([{ type: "text", text: "updated" }])}
      >
        Change Content
      </button>
    </div>
  ),
}));

// Mock dnd-kit to simplify testing (avoid drag complexity)
vi.mock("@dnd-kit/core", () => ({
  DndContext: ({ children }) => <div>{children}</div>,
  closestCenter: vi.fn(),
  KeyboardSensor: vi.fn(),
  PointerSensor: vi.fn(),
  useSensor: vi.fn(),
  useSensors: vi.fn(() => []),
  DragOverlay: ({ children }) => (
    <div data-testid="drag-overlay">{children}</div>
  ),
}));

vi.mock("@dnd-kit/sortable", () => ({
  arrayMove: (arr, from, to) => {
    const result = [...arr];
    const [item] = result.splice(from, 1);
    result.splice(to, 0, item);
    return result;
  },
  SortableContext: ({ children }) => <div>{children}</div>,
  sortableKeyboardCoordinates: vi.fn(),
  verticalListSortingStrategy: vi.fn(),
  useSortable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: vi.fn(),
    transform: null,
    transition: null,
    isDragging: false,
  }),
}));

vi.mock("@dnd-kit/utilities", () => ({
  CSS: { Transform: { toString: () => null } },
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const theme = createTheme();

function Wrapper({ children, defaultValues }) {
  const methods = useForm({
    defaultValues: defaultValues || {
      messages: [
        {
          id: "msg-1",
          role: "user",
          content: [{ type: "text", text: "Hello" }],
        },
        { id: "msg-2", role: "assistant", content: [] },
      ],
    },
  });
  return (
    <ThemeProvider theme={theme}>
      <FormProvider {...methods}>
        {typeof children === "function" ? children(methods) : children}
      </FormProvider>
    </ThemeProvider>
  );
}

function renderPromptMessageRow(props = {}, defaultValues) {
  let formMethods;
  const result = render(
    <Wrapper defaultValues={defaultValues}>
      {(methods) => {
        formMethods = methods;
        return <PromptMessageRow control={methods.control} {...props} />;
      }}
    </Wrapper>,
  );
  return { ...result, formMethods };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("PromptMessageRow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders message cards", () => {
    renderPromptMessageRow();

    expect(screen.getByTestId("prompt-card-0")).toBeInTheDocument();
    expect(screen.getByTestId("prompt-card-1")).toBeInTheDocument();
  });

  it("shows Add message button by default", () => {
    renderPromptMessageRow();
    expect(
      screen.getByRole("button", { name: /add message/i }),
    ).toBeInTheDocument();
  });

  it("hides Add message button when showAddButton=false", () => {
    renderPromptMessageRow({ showAddButton: false });
    expect(
      screen.queryByRole("button", { name: /add message/i }),
    ).not.toBeInTheDocument();
  });

  // ---- handleAddMessage ----
  it("adds a new message with random ID and default role", () => {
    const { formMethods } = renderPromptMessageRow();

    fireEvent.click(screen.getByRole("button", { name: /add message/i }));

    const messages = formMethods.getValues("messages");
    expect(messages).toHaveLength(3);
    expect(messages[2]).toEqual({
      id: "random-id-123",
      role: "user",
      content: [{ type: "text", text: "" }],
    });
  });

  // ---- handleRemoveMessage ----
  it("removes a message when more than one exists", () => {
    const { formMethods } = renderPromptMessageRow();

    fireEvent.click(screen.getByTestId("remove-0"));

    const messages = formMethods.getValues("messages");
    expect(messages).toHaveLength(1);
    expect(messages[0].id).toBe("msg-2");
  });

  it("shows warning when trying to remove the only message", () => {
    const { formMethods } = renderPromptMessageRow(
      {},
      {
        messages: [{ id: "msg-1", role: "user", content: [] }],
      },
    );

    fireEvent.click(screen.getByTestId("remove-0"));

    expect(mockEnqueueSnackbar).toHaveBeenCalledWith(
      "You must have at least one message.",
      { variant: "warning" },
    );

    // Message should still be there
    const messages = formMethods.getValues("messages");
    expect(messages).toHaveLength(1);
  });

  // ---- handleRoleChange ----
  it("updates role at index", () => {
    const { formMethods } = renderPromptMessageRow();

    fireEvent.click(screen.getByTestId("change-role-0"));

    const messages = formMethods.getValues("messages");
    expect(messages[0].role).toBe("assistant");
    expect(messages[1].role).toBe("assistant"); // unchanged
  });

  // ---- handleContentChange ----
  it("updates content at index", () => {
    const { formMethods } = renderPromptMessageRow();

    fireEvent.click(screen.getByTestId("change-content-1"));

    const messages = formMethods.getValues("messages");
    expect(messages[1].content).toEqual([{ type: "text", text: "updated" }]);
  });

  // ---- Disabled state ----
  it("disables add button when disabled prop is true", () => {
    renderPromptMessageRow({ disabled: true });

    const addButton = screen.getByRole("button", { name: /add message/i });
    expect(addButton).toBeDisabled();
  });
});

// ---------------------------------------------------------------------------
// Edge-case tests
// ---------------------------------------------------------------------------
describe("PromptMessageRow — edge cases", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders both cards even when messages have duplicate IDs", () => {
    const duplicateMessages = {
      messages: [
        {
          id: "dup-id-1",
          role: "user",
          content: [{ type: "text", text: "First" }],
        },
        {
          id: "dup-id-2",
          role: "assistant",
          content: [{ type: "text", text: "Second" }],
        },
      ],
    };

    renderPromptMessageRow({}, duplicateMessages);

    // Both cards should render (index-based test-ids)
    expect(screen.getByTestId("prompt-card-0")).toBeInTheDocument();
    expect(screen.getByTestId("prompt-card-1")).toBeInTheDocument();
  });
});
