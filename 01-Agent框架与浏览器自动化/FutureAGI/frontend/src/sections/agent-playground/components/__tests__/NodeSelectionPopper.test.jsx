import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import NodeSelectionPopper from "../NodeSelectionPopper";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
const mockAddNode = vi.fn();
vi.mock("../../AgentBuilder/hooks/useAddNodeOptimistic", () => ({
  default: () => ({ addNode: mockAddNode }),
}));

const mockTemplateNodes = [
  {
    id: "llm_prompt",
    node_template_id: "tpl-1",
    title: "LLM Prompt",
    description: "Run a prompt against an LLM",
    iconSrc: "/assets/icons/ic_chat_single.svg",
    color: "orange.500",
  },
  {
    id: "eval",
    node_template_id: "tpl-2",
    title: "Eval Node",
    description: "Run an evaluation",
    iconSrc: "/assets/icons/ic_eval.svg",
    color: "green.500",
  },
];

vi.mock("src/api/agent-playground/agent-playground", () => ({
  useGetNodeTemplates: () => ({ data: mockTemplateNodes }),
  useGetReferenceableGraphs: () => ({ data: [{ id: "other-agent" }] }),
}));

vi.mock("../../store", () => ({
  useAgentPlaygroundStoreShallow: () => ({ currentAgent: { id: "agent-1" } }),
}));

vi.mock("../../utils/constants", async () => {
  const actual = await vi.importActual("../../utils/constants");
  return {
    ...actual,
    AGENT_NODE: {
      id: "agent",
      title: "Agent Node",
      description: "Run an agent through LLM",
      iconSrc: "/assets/icons/navbar/ic_agents.svg",
      color: "blue.600",
    },
  };
});

// NodeCard mock: mirrors real behaviour — LLM_PROMPT triggers onExpandClick,
// all others trigger onNodeClick.
vi.mock("../NodeCard", () => ({
  default: ({ node, onNodeClick, onExpandClick, showExpandIcon }) => {
    const isPrompt = node.id === "llm_prompt" && showExpandIcon;
    return (
      <button
        data-testid={`node-card-${node.id}`}
        onClick={(e) => {
          if (isPrompt && onExpandClick) {
            onExpandClick(e);
          } else if (onNodeClick) {
            onNodeClick(node.id, node.node_template_id);
          }
        }}
      >
        {node.title}
      </button>
    );
  },
}));

// PromptNodePopper mock: renders only when open
vi.mock("../PromptNodePopper", () => ({
  default: ({ open, onNodeSelect, onClose }) =>
    open ? (
      <div data-testid="prompt-node-popper">
        <button
          data-testid="prompt-select-btn"
          onClick={() => onNodeSelect("llm_prompt", "tpl-1", { name: "Test" })}
        >
          Select prompt
        </button>
        <button data-testid="prompt-close-btn" onClick={onClose}>
          Close
        </button>
      </div>
    ) : null,
}));

vi.mock("notistack", () => ({
  enqueueSnackbar: vi.fn(),
}));

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("NodeSelectionPopper", () => {
  const anchorEl = document.createElement("div");
  const defaultProps = {
    open: true,
    anchorEl,
    onClose: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // -----------------------------------------------------------------------
  // Rendering
  // -----------------------------------------------------------------------
  it("renders template nodes plus the agent node when open", () => {
    render(<NodeSelectionPopper {...defaultProps} />);

    expect(screen.getByTestId("node-card-llm_prompt")).toBeInTheDocument();
    expect(screen.getByTestId("node-card-eval")).toBeInTheDocument();
    expect(screen.getByTestId("node-card-agent")).toBeInTheDocument();
  });

  it("does not render node cards when closed", () => {
    render(<NodeSelectionPopper {...defaultProps} open={false} />);

    expect(
      screen.queryByTestId("node-card-llm_prompt"),
    ).not.toBeInTheDocument();
    expect(screen.queryByTestId("node-card-eval")).not.toBeInTheDocument();
    expect(screen.queryByTestId("node-card-agent")).not.toBeInTheDocument();
  });

  // -----------------------------------------------------------------------
  // Non-LLM node click — with onNodeSelect callback
  // -----------------------------------------------------------------------
  it("calls onNodeSelect when provided and a non-LLM node is clicked", () => {
    const onNodeSelect = vi.fn();
    render(
      <NodeSelectionPopper {...defaultProps} onNodeSelect={onNodeSelect} />,
    );

    fireEvent.click(screen.getByTestId("node-card-eval"));

    expect(onNodeSelect).toHaveBeenCalledWith("eval", "tpl-2");
    expect(mockAddNode).not.toHaveBeenCalled();
  });

  // -----------------------------------------------------------------------
  // Non-LLM node click — without onNodeSelect (uses addNode)
  // -----------------------------------------------------------------------
  it("calls addNode when onNodeSelect is not provided and a non-LLM node is clicked", () => {
    render(<NodeSelectionPopper {...defaultProps} />);

    fireEvent.click(screen.getByTestId("node-card-eval"));

    expect(mockAddNode).toHaveBeenCalledWith({
      type: "eval",
      position: undefined,
      node_template_id: "tpl-2",
    });
  });

  it("calls onClose after clicking a non-LLM node", () => {
    render(<NodeSelectionPopper {...defaultProps} />);

    fireEvent.click(screen.getByTestId("node-card-eval"));

    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  // -----------------------------------------------------------------------
  // LLM_PROMPT node click — opens PromptNodePopper
  // -----------------------------------------------------------------------
  it("opens PromptNodePopper when an LLM_PROMPT node is clicked", () => {
    render(<NodeSelectionPopper {...defaultProps} />);

    // PromptNodePopper should not be visible initially
    expect(screen.queryByTestId("prompt-node-popper")).not.toBeInTheDocument();

    // Click the llm_prompt card — triggers onExpandClick, which opens PromptNodePopper
    fireEvent.click(screen.getByTestId("node-card-llm_prompt"));

    expect(screen.getByTestId("prompt-node-popper")).toBeInTheDocument();
  });

  it("does not call addNode or onNodeSelect when LLM_PROMPT node is clicked", () => {
    const onNodeSelect = vi.fn();
    render(
      <NodeSelectionPopper {...defaultProps} onNodeSelect={onNodeSelect} />,
    );

    fireEvent.click(screen.getByTestId("node-card-llm_prompt"));

    expect(mockAddNode).not.toHaveBeenCalled();
    expect(onNodeSelect).not.toHaveBeenCalled();
  });

  // -----------------------------------------------------------------------
  // PromptNodePopper interaction — with onNodeSelect
  // -----------------------------------------------------------------------
  it("delegates to onNodeSelect from PromptNodePopper when onNodeSelect is provided", async () => {
    const onNodeSelect = vi.fn();
    render(
      <NodeSelectionPopper {...defaultProps} onNodeSelect={onNodeSelect} />,
    );

    // Open the prompt popper
    fireEvent.click(screen.getByTestId("node-card-llm_prompt"));

    // Select a prompt node inside the popper
    fireEvent.click(screen.getByTestId("prompt-select-btn"));

    expect(onNodeSelect).toHaveBeenCalledWith("llm_prompt", "tpl-1", {
      name: "Test",
    });
  });

  // -----------------------------------------------------------------------
  // PromptNodePopper interaction — without onNodeSelect (uses addNode)
  // -----------------------------------------------------------------------
  it("calls addNode from PromptNodePopper when onNodeSelect is not provided", () => {
    render(<NodeSelectionPopper {...defaultProps} />);

    // Open the prompt popper
    fireEvent.click(screen.getByTestId("node-card-llm_prompt"));

    // Select a prompt node inside the popper
    fireEvent.click(screen.getByTestId("prompt-select-btn"));

    expect(mockAddNode).toHaveBeenCalledWith({
      type: "llm_prompt",
      position: undefined,
      node_template_id: "tpl-1",
      name: "Test",
      config: { name: "Test" },
    });
  });

  // -----------------------------------------------------------------------
  // Agent node click
  // -----------------------------------------------------------------------
  it("calls addNode for agent node with no node_template_id", () => {
    render(<NodeSelectionPopper {...defaultProps} />);

    fireEvent.click(screen.getByTestId("node-card-agent"));

    expect(mockAddNode).toHaveBeenCalledWith({
      type: "agent",
      position: undefined,
      node_template_id: undefined,
    });
  });
});

// ---------------------------------------------------------------------------
// Edge-case tests
// ---------------------------------------------------------------------------
describe("NodeSelectionPopper — edge cases", () => {
  const anchorEl = document.createElement("div");
  const defaultProps = {
    open: true,
    anchorEl,
    onClose: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("handles rapid successive clicks on a non-LLM node", () => {
    render(<NodeSelectionPopper {...defaultProps} />);

    const card = screen.getByTestId("node-card-eval");

    fireEvent.click(card);
    fireEvent.click(card);

    // First click closes the popper (handleMainClose), so the second click
    // may or may not register depending on render. At minimum the first fires.
    expect(mockAddNode).toHaveBeenCalled();
  });

  it("handles rapid successive clicks on LLM_PROMPT without triggering addNode", () => {
    const onNodeSelect = vi.fn();
    render(
      <NodeSelectionPopper {...defaultProps} onNodeSelect={onNodeSelect} />,
    );

    const card = screen.getByTestId("node-card-llm_prompt");
    fireEvent.click(card);
    fireEvent.click(card);

    expect(mockAddNode).not.toHaveBeenCalled();
    expect(onNodeSelect).not.toHaveBeenCalled();
  });

  it("closes PromptNodePopper via its onClose callback", () => {
    render(<NodeSelectionPopper {...defaultProps} />);

    // Open the prompt popper
    fireEvent.click(screen.getByTestId("node-card-llm_prompt"));
    expect(screen.getByTestId("prompt-node-popper")).toBeInTheDocument();

    // Close it
    fireEvent.click(screen.getByTestId("prompt-close-btn"));
    expect(screen.queryByTestId("prompt-node-popper")).not.toBeInTheDocument();
  });

  it("renders all three nodes in order (templates + agent)", () => {
    render(<NodeSelectionPopper {...defaultProps} />);

    const cards = screen.getAllByTestId(/^node-card-/);
    expect(cards).toHaveLength(3);
    // Templates come first, AGENT_NODE is appended last
    expect(cards[0]).toHaveAttribute("data-testid", "node-card-llm_prompt");
    expect(cards[1]).toHaveAttribute("data-testid", "node-card-eval");
    expect(cards[2]).toHaveAttribute("data-testid", "node-card-agent");
  });
});
