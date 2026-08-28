import PropTypes from "prop-types";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "src/utils/test-utils";
import useFalconStore from "../store/useFalconStore";
import MessageList from "../components/MessageList";

// Mock scrollTo for jsdom
Element.prototype.scrollTo = vi.fn();

// Mock Iconify
function MockIconify({ icon, ...props }) {
  return <span data-testid="iconify" data-icon={icon} {...props} />;
}

MockIconify.propTypes = {
  icon: PropTypes.string.isRequired,
};

vi.mock("src/components/iconify", () => ({
  default: MockIconify,
}));

// Mock UserMessage — renders content directly for easy assertion
vi.mock("../components/UserMessage", () => ({
  default: ({ message }) => (
    <div data-testid="user-message">{message.content}</div>
  ),
}));

// Mock AssistantMessage — renders content + tool calls for easy assertion
vi.mock("../components/AssistantMessage", () => ({
  default: ({ message }) => (
    <div data-testid="assistant-message">
      <span>{message.content}</span>
      {(message.tool_calls || []).map((tc) => (
        <div
          key={tc.call_id}
          data-testid="tool-call-card"
          data-tool={tc.tool_name}
        >
          {tc.tool_name}
        </div>
      ))}
    </div>
  ),
}));

// Mock QuickActions
vi.mock("../components/QuickActions", () => ({
  default: ({ onAction }) => (
    <div data-testid="quick-actions">
      <button type="button" onClick={() => onAction?.("Build a dataset")}>
        Build a dataset
      </button>
    </div>
  ),
}));

beforeEach(() => {
  useFalconStore.getState().resetAll();
});

describe("MessageList", () => {
  it("renders empty state when no messages", () => {
    render(<MessageList onQuickAction={vi.fn()} onFeedback={vi.fn()} />);
    expect(screen.getByText("How can I help?")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Ask about your data, evaluations, experiments, traces, and more.",
      ),
    ).toBeInTheDocument();
  });

  it("renders quick actions in empty state", () => {
    render(<MessageList onQuickAction={vi.fn()} onFeedback={vi.fn()} />);
    expect(screen.getByText("Build a dataset")).toBeInTheDocument();
  });

  it("renders user messages", () => {
    useFalconStore.getState().addMessage({
      id: "u1",
      role: "user",
      content: "Hello from user",
    });
    render(<MessageList onQuickAction={vi.fn()} onFeedback={vi.fn()} />);
    expect(screen.getByText("Hello from user")).toBeInTheDocument();
    expect(screen.getByTestId("user-message")).toBeInTheDocument();
  });

  it("renders assistant messages", () => {
    useFalconStore.getState().addMessage({
      id: "a1",
      role: "assistant",
      content: "Hi, I am Falcon AI",
    });
    render(<MessageList onQuickAction={vi.fn()} onFeedback={vi.fn()} />);
    expect(screen.getByText("Hi, I am Falcon AI")).toBeInTheDocument();
    expect(screen.getByTestId("assistant-message")).toBeInTheDocument();
  });

  it("renders mix of user and assistant messages in order", () => {
    useFalconStore.getState().addMessage({
      id: "u1",
      role: "user",
      content: "Question",
    });
    useFalconStore.getState().addMessage({
      id: "a1",
      role: "assistant",
      content: "Answer",
    });
    render(<MessageList onQuickAction={vi.fn()} onFeedback={vi.fn()} />);
    expect(screen.getByText("Question")).toBeInTheDocument();
    expect(screen.getByText("Answer")).toBeInTheDocument();
  });

  it("does not show empty state when messages exist", () => {
    useFalconStore.getState().addMessage({
      id: "u1",
      role: "user",
      content: "Hi",
    });
    render(<MessageList onQuickAction={vi.fn()} onFeedback={vi.fn()} />);
    expect(screen.queryByText("How can I help?")).not.toBeInTheDocument();
  });

  it("renders tool call cards on assistant messages", () => {
    useFalconStore.getState().addMessage({
      id: "a1",
      role: "assistant",
      content: "Here are the results",
      tool_calls: [
        {
          call_id: "tc_1",
          tool_name: "search_traces",
          status: "completed",
          result_summary: "Found 5 traces",
          step: 1,
        },
      ],
    });
    render(<MessageList onQuickAction={vi.fn()} onFeedback={vi.fn()} />);
    expect(screen.getByTestId("tool-call-card")).toBeInTheDocument();
    expect(screen.getByText("search_traces")).toBeInTheDocument();
  });
});
