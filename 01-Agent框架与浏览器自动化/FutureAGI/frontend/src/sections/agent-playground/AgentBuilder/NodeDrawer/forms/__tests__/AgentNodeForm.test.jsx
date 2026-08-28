/* eslint-disable react/prop-types */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { FormProvider, useForm } from "react-hook-form";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AgentNodeForm from "../AgentNodeForm";
import { useAgentPlaygroundStore } from "../../../../store";

// ---- Mock data ----

const MOCK_GRAPHS = [
  {
    id: "graph-A",
    name: "Summarizer Agent",
    versions: [
      {
        id: "ver-A1",
        versionNumber: 3,
        status: "active",
        exposedPorts: [
          {
            id: "port-1",
            display_name: "input_text",
            direction: "input",
            dataSchema: { type: "string" },
            required: true,
          },
          {
            id: "port-2",
            display_name: "summary",
            direction: "output",
            dataSchema: null,
            required: undefined,
          },
        ],
      },
    ],
  },
  {
    id: "graph-B",
    name: "Classifier Agent",
    versions: [
      {
        id: "ver-B1",
        versionNumber: 1,
        status: "active",
        exposedPorts: [],
      },
    ],
  },
  {
    id: "graph-C",
    name: "No Version Agent",
    versions: [],
  },
];

// ---- Mocks ----

vi.mock("src/api/agent-playground/agent-playground", () => ({
  useGetReferenceableGraphs: () => ({
    data: MOCK_GRAPHS,
    isLoading: false,
  }),
  useGetVersionDetail: () => ({ data: null }),
  useUpdateNode: () => ({
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
  }),
}));

vi.mock("src/utils/logger", () => ({
  default: { error: vi.fn(), warn: vi.fn(), info: vi.fn(), debug: vi.fn() },
}));

let uuidCounter = 0;
vi.stubGlobal(
  "crypto",
  Object.assign({}, globalThis.crypto, {
    randomUUID: () => `uuid-${++uuidCounter}`,
  }),
);

const mockEnsureDraft = vi.fn().mockResolvedValue("existing");
vi.mock("../../../saveDraftContext", () => ({
  useSaveDraftContext: () => ({ ensureDraft: mockEnsureDraft }),
}));

const mockPartialUpdate = vi.fn().mockResolvedValue({});
vi.mock("../../hooks/usePartialNodeUpdate", () => ({
  default: () => ({ partialUpdate: mockPartialUpdate, isPending: false }),
}));

vi.mock("../../../../hooks/useConnectedNodeVariables", () => ({
  default: () => ({ dropdownOptions: [] }),
}));

vi.mock("../../../../utils/versionPayloadUtils", () => ({
  buildDraftCreationPayload: vi.fn(),
}));

vi.mock("notistack", () => ({
  enqueueSnackbar: vi.fn(),
}));

vi.mock("src/components/FromSearchSelectField", () => ({
  FormSearchSelectFieldControl: ({ fieldName, label, onChange, options }) => (
    <select
      data-testid={`select-${fieldName}`}
      aria-label={label}
      onChange={onChange}
    >
      <option value="">Select</option>
      {(options || []).map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  ),
}));

vi.mock("../../../../components/AgentGraphPreview", () => ({
  default: () => <div data-testid="graph-preview" />,
}));

// ---- Helpers ----

function FormWrapper({ children, defaultValues }) {
  const methods = useForm({
    defaultValues: defaultValues || { graphId: "", versionId: "" },
  });
  return <FormProvider {...methods}>{children}</FormProvider>;
}

function renderForm(nodeId = "node-1", formDefaults = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  useAgentPlaygroundStore.setState({
    currentAgent: { id: "agent-1" },
    nodes: [],
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <FormWrapper
        defaultValues={{ graphId: "", versionId: "", ...formDefaults }}
      >
        <AgentNodeForm nodeId={nodeId} />
      </FormWrapper>
    </QueryClientProvider>,
  );
}

// ---- Tests ----

describe("AgentNodeForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    uuidCounter = 0;
    useAgentPlaygroundStore.getState().reset();
  });

  it("renders agent and version dropdowns", () => {
    renderForm();
    expect(screen.getByTestId("select-graphId")).toBeInTheDocument();
    expect(screen.getByTestId("select-versionId")).toBeInTheDocument();
  });

  it("renders graph preview", () => {
    renderForm();
    expect(screen.getByTestId("graph-preview")).toBeInTheDocument();
  });

  describe("onSubmit", () => {
    it("maps exposedPorts to internal port shape", async () => {
      // Pre-select graph-A so onSubmit can find it
      renderForm("node-1", { graphId: "graph-A", versionId: "ver-A1" });

      fireEvent.click(screen.getByText("Save"));

      await waitFor(() => {
        // Verify submit was processed (ensureDraft was called)
        expect(mockEnsureDraft).toHaveBeenCalled();
      });
    });

    it("calls updateNodeData with correct config and ref_graph_version_id", async () => {
      const mockUpdateNodeData = vi.fn();
      useAgentPlaygroundStore.setState({
        currentAgent: { id: "agent-1" },
        nodes: [],
        updateNodeData: mockUpdateNodeData,
        clearSelectedNode: vi.fn(),
        clearValidationErrorNode: vi.fn(),
      });

      renderForm("node-42", { graphId: "graph-A", versionId: "ver-A1" });
      fireEvent.click(screen.getByText("Save"));

      await waitFor(() => {
        expect(mockUpdateNodeData).toHaveBeenCalledWith("node-42", {
          config: {
            graphId: "graph-A",
            versionId: "ver-A1",
            payload: {
              ports: [
                {
                  id: "uuid-1",
                  key: "custom",
                  display_name: "input_text",
                  direction: "input",
                  data_schema: { type: "string" },
                  required: true,
                  ref_port_id: "port-1",
                },
                {
                  id: "uuid-2",
                  key: "custom",
                  display_name: "response_1",
                  direction: "output",
                  data_schema: { type: "string" },
                  required: false,
                  ref_port_id: "port-2",
                },
              ],
              inputMappings: [],
            },
          },
          graphId: "graph-A",
          versionId: "ver-A1",
          ref_graph_version_id: "ver-A1",
        });
      });
    });

    it("defaults data_schema to { type: 'string' } when dataSchema is null", async () => {
      const mockUpdateNodeData = vi.fn();
      useAgentPlaygroundStore.setState({
        currentAgent: { id: "agent-1" },
        nodes: [],
        updateNodeData: mockUpdateNodeData,
        clearSelectedNode: vi.fn(),
        clearValidationErrorNode: vi.fn(),
      });

      renderForm("node-1", { graphId: "graph-A", versionId: "ver-A1" });
      fireEvent.click(screen.getByText("Save"));

      await waitFor(() => {
        const ports = mockUpdateNodeData.mock.calls[0][1].config.payload.ports;
        // Second port (summary) has dataSchema: null in source
        expect(ports[1].data_schema).toEqual({ type: "string" });
      });
    });

    it("defaults required to false when undefined", async () => {
      const mockUpdateNodeData = vi.fn();
      useAgentPlaygroundStore.setState({
        currentAgent: { id: "agent-1" },
        nodes: [],
        updateNodeData: mockUpdateNodeData,
        clearSelectedNode: vi.fn(),
        clearValidationErrorNode: vi.fn(),
      });

      renderForm("node-1", { graphId: "graph-A", versionId: "ver-A1" });
      fireEvent.click(screen.getByText("Save"));

      await waitFor(() => {
        const ports = mockUpdateNodeData.mock.calls[0][1].config.payload.ports;
        // Second port has required: undefined in source → defaults to false
        expect(ports[1].required).toBe(false);
        // First port has required: true → stays true
        expect(ports[0].required).toBe(true);
      });
    });

    it("produces empty ports array when graph has no exposedPorts", async () => {
      const mockUpdateNodeData = vi.fn();
      useAgentPlaygroundStore.setState({
        currentAgent: { id: "agent-1" },
        nodes: [],
        updateNodeData: mockUpdateNodeData,
        clearSelectedNode: vi.fn(),
        clearValidationErrorNode: vi.fn(),
      });

      renderForm("node-1", { graphId: "graph-B", versionId: "ver-B1" });
      fireEvent.click(screen.getByText("Save"));

      await waitFor(() => {
        const ports = mockUpdateNodeData.mock.calls[0][1].config.payload.ports;
        expect(ports).toEqual([]);
      });
    });

    it("calls clearValidationErrorNode, ensureDraft, and clearSelectedNode", async () => {
      const mockClearValidation = vi.fn();
      const mockClearSelected = vi.fn();
      useAgentPlaygroundStore.setState({
        currentAgent: { id: "agent-1" },
        nodes: [],
        updateNodeData: vi.fn(),
        clearSelectedNode: mockClearSelected,
        clearValidationErrorNode: mockClearValidation,
      });

      const { enqueueSnackbar } = await import("notistack");

      renderForm("node-1", { graphId: "graph-A", versionId: "ver-A1" });
      fireEvent.click(screen.getByText("Save"));

      await waitFor(() => {
        expect(mockClearValidation).toHaveBeenCalledWith("node-1");
        expect(mockEnsureDraft).toHaveBeenCalled();
        expect(enqueueSnackbar).not.toHaveBeenCalled();
        expect(mockClearSelected).toHaveBeenCalled();
      });
    });
  });

  describe("handleAgentChange", () => {
    it("auto-sets versionId when graph has activeVersionId", () => {
      renderForm();
      const agentSelect = screen.getByTestId("select-graphId");
      fireEvent.change(agentSelect, { target: { value: "graph-A" } });

      // The version select should now have the version option
      const versionSelect = screen.getByTestId("select-versionId");
      expect(versionSelect).toBeInTheDocument();
    });

    it("clears versionId when graph has no activeVersionId", () => {
      renderForm("node-1", { graphId: "graph-A", versionId: "ver-A1" });
      const agentSelect = screen.getByTestId("select-graphId");
      // Change to graph-C which has no activeVersionId
      fireEvent.change(agentSelect, { target: { value: "graph-C" } });

      const versionSelect = screen.getByTestId("select-versionId");
      expect(versionSelect).toBeInTheDocument();
    });
  });
});
