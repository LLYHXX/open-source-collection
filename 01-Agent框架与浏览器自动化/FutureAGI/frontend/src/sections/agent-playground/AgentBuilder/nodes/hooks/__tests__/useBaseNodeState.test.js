import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import useBaseNodeState from "../useBaseNodeState";
import {
  useAgentPlaygroundStore,
  useWorkflowRunStore,
} from "../../../../store";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
const mockUseNodeId = vi.fn(() => "n1");
const mockUseNodeConnections = vi.fn(() => []);

vi.mock("@xyflow/react", () => ({
  useNodeId: (...args) => mockUseNodeId(...args),
  useNodeConnections: (...args) => mockUseNodeConnections(...args),
}));

vi.mock("../../../saveDraftContext", () => ({
  useSaveDraftContext: () => ({ saveDraft: vi.fn() }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function makeData(overrides = {}) {
  return {
    preview: false,
    config: { payload: {} },
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("useBaseNodeState", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseNodeId.mockReturnValue("n1");
    mockUseNodeConnections.mockReturnValue([]);
    useAgentPlaygroundStore.getState().reset();
    useWorkflowRunStore.getState().reset();
  });

  // ---- Node height ----
  it("returns NODE_MIN_HEIGHT as nodeHeight", () => {
    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.nodeHeight).toBe(40);
  });

  // ---- Execution state derivation ----
  it("derives isIdleState when no execution state", () => {
    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.isIdleState).toBe(true);
    expect(result.current.isRunning).toBe(false);
    expect(result.current.isCompleted).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it("derives isRunning when execution state is running", () => {
    useAgentPlaygroundStore.setState({
      nodeExecutionStates: { n1: "running" },
    });

    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.isRunning).toBe(true);
    expect(result.current.isIdleState).toBe(false);
  });

  it("derives isCompleted when execution state is completed", () => {
    useAgentPlaygroundStore.setState({
      nodeExecutionStates: { n1: "completed" },
    });

    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.isCompleted).toBe(true);
  });

  it("derives isError when execution state is error", () => {
    useAgentPlaygroundStore.setState({
      nodeExecutionStates: { n1: "error" },
    });

    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.isError).toBe(true);
  });

  // ---- Preview mode ----
  it("returns empty store values in preview mode", () => {
    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData({ preview: true }) }),
    );

    expect(result.current.preview).toBe(true);
    expect(result.current.selected).toBeUndefined();
    expect(result.current.setSelectedNode).toBeUndefined();
  });

  // ---- Selected state ----
  it("returns selected=true when node is selected in store", () => {
    useAgentPlaygroundStore.setState({
      selectedNode: { id: "n1" },
    });

    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.selected).toBe(true);
  });

  it("returns selected=false when different node is selected", () => {
    useAgentPlaygroundStore.setState({
      selectedNode: { id: "n2" },
    });

    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.selected).toBe(false);
  });

  // ---- Validation error ----
  it("returns hasValidationError when node is in error list", () => {
    useAgentPlaygroundStore.setState({
      validationErrorNodeIds: ["n1", "n3"],
    });

    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.hasValidationError).toBe(true);
  });

  // ---- Outgoing edge via useNodeConnections ----
  it("returns hasOutgoingEdge when node has outgoing connections", () => {
    // useNodeConnections is called twice: once for target (incoming), once for source (outgoing)
    mockUseNodeConnections
      .mockReturnValueOnce([]) // incoming: none
      .mockReturnValueOnce([{ source: "n1", target: "n2" }]); // outgoing: one

    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.hasOutgoingEdge).toBe(true);
  });

  it("returns hasOutgoingEdge=false when node has no outgoing connections", () => {
    mockUseNodeConnections.mockReturnValue([]);

    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.hasOutgoingEdge).toBe(false);
  });

  // ---- Incoming edge via useNodeConnections ----
  it("returns hasIncomingEdge when node has incoming connections", () => {
    mockUseNodeConnections
      .mockReturnValueOnce([{ source: "n0", target: "n1" }]) // incoming: one
      .mockReturnValueOnce([]); // outgoing: none

    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.hasIncomingEdge).toBe(true);
  });

  // ---- useNodeId called ----
  it("calls useNodeId to get context node id", () => {
    renderHook(() => useBaseNodeState({ id: "n1", data: makeData() }));

    expect(mockUseNodeId).toHaveBeenCalled();
  });

  // ---- isWorkflowRunning ----
  it("returns isWorkflowRunning from workflow store", () => {
    useWorkflowRunStore.setState({ isRunning: true });

    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.isWorkflowRunning).toBe(true);
  });

  // ---- Connections fallback when no node context ----
  it("returns hasOutgoingEdge=false when useNodeId returns null", () => {
    mockUseNodeId.mockReturnValue(null);
    mockUseNodeConnections.mockReturnValue([{ source: "n1", target: "n2" }]);

    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    // When contextNodeId is null, EMPTY_CONNECTIONS is used instead
    expect(result.current.hasOutgoingEdge).toBe(false);
    expect(result.current.hasIncomingEdge).toBe(false);
  });

  // ---- deleteNode and setSelectedNode are returned ----
  it("returns setSelectedNode and deleteNode from store", () => {
    const { result } = renderHook(() =>
      useBaseNodeState({ id: "n1", data: makeData() }),
    );

    expect(result.current.setSelectedNode).toBeDefined();
    expect(result.current.deleteNode).toBeDefined();
  });
});

// ---------------------------------------------------------------------------
// Edge-case tests
// ---------------------------------------------------------------------------
describe("useBaseNodeState — edge cases", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseNodeId.mockReturnValue("n1");
    mockUseNodeConnections.mockReturnValue([]);
    useAgentPlaygroundStore.getState().reset();
    useWorkflowRunStore.getState().reset();
  });

  it("returns nodeHeight as NODE_MIN_HEIGHT regardless of data shape", () => {
    const data = {
      preview: false,
      config: {}, // config exists, but no payload
    };

    const { result } = renderHook(() => useBaseNodeState({ id: "n1", data }));

    expect(result.current.nodeHeight).toBe(40); // NODE_MIN_HEIGHT
  });

  it("handles config.payload with no ports key gracefully", () => {
    const data = {
      preview: false,
      config: { payload: { someOtherKey: "value" } },
    };

    const { result } = renderHook(() => useBaseNodeState({ id: "n1", data }));

    expect(result.current.nodeHeight).toBe(40); // NODE_MIN_HEIGHT
  });
});
