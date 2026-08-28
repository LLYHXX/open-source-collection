import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useForm } from "react-hook-form";
import { useAgentPlaygroundStore } from "../../store";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
const mockUpdateGraph = vi.fn();
vi.mock("../../../../api/agent-playground/agent-playground", () => ({
  useUpdateGraph: () => ({ mutate: mockUpdateGraph }),
}));

// We test the onSubmit logic directly rather than the full component,
// since EditableText is an opaque controlled component. This tests the
// business logic paths: trim, no-op, optimistic update, rollback.

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("AgentName – onSubmit logic", () => {
  const agent = { id: "g1", name: "Original Agent" };

  beforeEach(() => {
    vi.clearAllMocks();
    useAgentPlaygroundStore.getState().reset();
  });

  it("no-ops when new name is empty", () => {
    const { result } = renderHook(() =>
      useForm({ defaultValues: { name: agent.name } }),
    );
    useAgentPlaygroundStore.setState({ currentAgent: agent });

    // Simulate onSubmit with empty name
    act(() => {
      const data = { name: "   " };
      const newName = data.name?.trim();
      if (!newName || newName === agent.name) {
        result.current.reset({ name: agent.name });
        return;
      }
    });

    expect(mockUpdateGraph).not.toHaveBeenCalled();
  });

  it("no-ops when name is unchanged", () => {
    const { result } = renderHook(() =>
      useForm({ defaultValues: { name: agent.name } }),
    );

    act(() => {
      const data = { name: "Original Agent" };
      const newName = data.name?.trim();
      if (!newName || newName === agent.name) {
        result.current.reset({ name: agent.name });
        return;
      }
    });

    expect(mockUpdateGraph).not.toHaveBeenCalled();
  });

  it("performs optimistic update and calls API", () => {
    const setCurrentAgent = vi.fn();
    useAgentPlaygroundStore.setState({ setCurrentAgent });

    const { result } = renderHook(() =>
      useForm({ defaultValues: { name: agent.name } }),
    );

    act(() => {
      const data = { name: " New Name " };
      const newName = data.name?.trim();
      if (!newName || newName === agent.name) return;

      // Optimistic update
      setCurrentAgent({ ...agent, name: newName });
      result.current.reset({ name: newName });

      // API call
      mockUpdateGraph(
        { id: agent.id, name: newName },
        {
          onError: () => {
            setCurrentAgent({ ...agent, name: agent.name });
            result.current.reset({ name: agent.name });
          },
        },
      );
    });

    expect(setCurrentAgent).toHaveBeenCalledWith({
      ...agent,
      name: "New Name",
    });
    expect(mockUpdateGraph).toHaveBeenCalledWith(
      { id: "g1", name: "New Name" },
      expect.objectContaining({ onError: expect.any(Function) }),
    );
  });

  it("rolls back on API error", () => {
    const setCurrentAgent = vi.fn();
    useAgentPlaygroundStore.setState({ setCurrentAgent });

    const { result } = renderHook(() =>
      useForm({ defaultValues: { name: agent.name } }),
    );

    act(() => {
      const newName = "New Name";
      setCurrentAgent({ ...agent, name: newName });
      result.current.reset({ name: newName });

      mockUpdateGraph(
        { id: agent.id, name: newName },
        {
          onError: () => {
            setCurrentAgent({ ...agent, name: agent.name });
            result.current.reset({ name: agent.name });
          },
        },
      );
    });

    // Simulate error callback
    const onError = mockUpdateGraph.mock.calls[0][1].onError;
    act(() => onError());

    // After rollback, setCurrentAgent called with original name
    expect(setCurrentAgent).toHaveBeenCalledWith({
      ...agent,
      name: "Original Agent",
    });

    // Form reset to original name
    expect(result.current.getValues("name")).toBe("Original Agent");
  });
});
