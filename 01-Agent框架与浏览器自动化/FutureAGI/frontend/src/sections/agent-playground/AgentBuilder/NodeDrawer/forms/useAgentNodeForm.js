import { useEffect, useMemo } from "react";
import { useFormContext, useWatch } from "react-hook-form";
import { useQueryClient } from "@tanstack/react-query";
import { enqueueSnackbar } from "notistack";
import {
  useGetReferenceableGraphs,
  useGetVersionDetail,
} from "src/api/agent-playground/agent-playground";
import {
  useAgentPlaygroundStoreShallow,
  generateOutputLabel,
} from "../../../store";
import { PORT_DIRECTION, PORT_KEYS } from "../../../utils/constants";
import usePartialNodeUpdate from "../../hooks/usePartialNodeUpdate";
import { useSaveDraftContext } from "../../saveDraftContext";
import useConnectedNodeVariables from "../../../hooks/useConnectedNodeVariables";
import logger from "src/utils/logger";

export function useAgentNodeForm(nodeId) {
  const queryClient = useQueryClient();
  const { control, setValue, handleSubmit } = useFormContext();

  const {
    updateNodeData,
    clearSelectedNode,
    clearValidationErrorNode,
    currentAgent,
    nodes,
  } = useAgentPlaygroundStoreShallow((state) => ({
    updateNodeData: state.updateNodeData,
    clearSelectedNode: state.clearSelectedNode,
    clearValidationErrorNode: state.clearValidationErrorNode,
    currentAgent: state.currentAgent,
    nodes: state.nodes,
  }));
  const { partialUpdate, isPending } = usePartialNodeUpdate();
  const { ensureDraft } = useSaveDraftContext();
  const { dropdownOptions } = useConnectedNodeVariables(nodeId, {
    includeDatasetVars: false,
  });

  // Watch selected agent and version
  const selectedGraphId = useWatch({ control, name: "graphId" });
  const selectedVersionId = useWatch({ control, name: "versionId" });

  // Fetch referenceable graphs for the current agent
  const { data: referenceableGraphs, isLoading: isLoadingGraphs } =
    useGetReferenceableGraphs(currentAgent?.id);

  // Fetch version detail for the selected agent+version (reused by AgentGraphPreview)
  const { data: versionDetailData } = useGetVersionDetail(
    selectedGraphId,
    selectedVersionId,
  );

  // Derive input ports from the selected version's exposedPorts
  const inputPorts = useMemo(() => {
    if (!selectedGraphId || !selectedVersionId || !referenceableGraphs)
      return [];
    const graph = referenceableGraphs.find((g) => g.id === selectedGraphId);
    const version = graph?.versions?.find((v) => v.id === selectedVersionId);
    if (!version?.exposedPorts) return [];
    return version.exposedPorts.filter(
      (p) => p.direction === PORT_DIRECTION.INPUT,
    );
  }, [selectedGraphId, selectedVersionId, referenceableGraphs]);

  // Build variable options for mapping dropdowns
  const variableOptions = useMemo(
    () =>
      dropdownOptions.map((opt) => ({
        label: opt.value,
        value: opt.value,
      })),
    [dropdownOptions],
  );

  // Clear stale input mapping values when available options change
  const watchedInputMappings = useWatch({ control, name: "inputMappings" });
  useEffect(() => {
    if (!watchedInputMappings?.length || !variableOptions.length) return;
    const validValues = new Set(variableOptions.map((o) => o.value));
    watchedInputMappings.forEach((mapping, index) => {
      if (mapping.value && !validValues.has(mapping.value)) {
        setValue(`inputMappings.${index}.value`, null);
      }
    });
  }, [variableOptions, watchedInputMappings, setValue]);

  // Transform graphs to dropdown options
  const agentOptions = useMemo(() => {
    if (isLoadingGraphs || !referenceableGraphs) return [];
    return referenceableGraphs.map((graph) => ({
      label: graph.name,
      value: graph.id,
    }));
  }, [referenceableGraphs, isLoadingGraphs]);

  // Build version dropdown from all versions in the selected graph
  const versionOptions = useMemo(() => {
    if (!selectedGraphId || !referenceableGraphs) return [];
    const graph = referenceableGraphs.find((g) => g.id === selectedGraphId);
    if (!graph?.versions?.length) return [];
    return graph.versions.map((v) => ({
      label: `Version ${v.version_number}`,
      value: v.id,
    }));
  }, [selectedGraphId, referenceableGraphs]);

  // Build inputMappings with keys from a version's exposed input ports
  const buildInputMappings = (graphId, versionId) => {
    const graph = referenceableGraphs?.find((g) => g.id === graphId);
    const version = graph?.versions?.find((v) => v.id === versionId);
    if (!version?.exposedPorts) return [];
    return version.exposedPorts
      .filter((p) => p.direction === PORT_DIRECTION.INPUT)
      .map((p) => ({ key: p.display_name, value: null }));
  };

  // Reset version and input mappings when agent changes
  const handleAgentChange = (e) => {
    const newGraphId = e?.target?.value;
    const graph = referenceableGraphs?.find((g) => g.id === newGraphId);
    const firstVersionId = graph?.versions?.[0]?.id || "";
    setValue("graphId", newGraphId);
    setValue("versionId", firstVersionId);
    setValue("inputMappings", buildInputMappings(newGraphId, firstVersionId));
  };

  // Clear input mappings when version changes (ports may differ)
  const handleVersionChange = (e) => {
    const newVersionId = e?.target?.value;
    setValue("versionId", newVersionId);
    setValue(
      "inputMappings",
      buildInputMappings(selectedGraphId, newVersionId),
    );
  };

  const onSubmit = handleSubmit(
    async (formData) => {
      const selectedGraph = referenceableGraphs?.find(
        (g) => g.id === formData.graphId,
      );
      const selectedVersion = selectedGraph?.versions?.find(
        (v) => v.id === formData.versionId,
      );

      // Map exposedPorts from the selected version to our port shape.
      // Output ports get sequential display_names (response_N) unique across the graph,
      // matching the pattern used by addOptimisticNode in the store.
      let nextOutputLabel = generateOutputLabel(nodes);
      const ports = (selectedVersion?.exposedPorts || []).map((p) => {
        const baseName = (p.display_name || "").replace(/_[a-z0-9]{9}$/, "");
        const tempId = crypto.randomUUID();

        let displayName;
        if (p.direction === PORT_DIRECTION.OUTPUT) {
          displayName = nextOutputLabel;
          const num = parseInt(nextOutputLabel.split("_").pop(), 10);
          nextOutputLabel = `response_${num + 1}`;
        } else {
          displayName = baseName;
        }

        return {
          id: tempId,
          key: PORT_KEYS.CUSTOM,
          display_name: displayName,
          direction: p.direction,
          data_schema: p.dataSchema || { type: "string" },
          required: p.required ?? false,
          ref_port_id: p.id,
        };
      });

      const nodeUpdate = {
        config: {
          ...formData,
          payload: {
            ports,
            inputMappings: formData.inputMappings || [],
          },
        },
        graphId: formData.graphId,
        versionId: formData.versionId,
        ref_graph_version_id: formData.versionId,
      };

      clearValidationErrorNode(nodeId);
      const prevData = nodes.find((n) => n.id === nodeId)?.data;

      // Always apply optimistic update first
      updateNodeData(nodeId, nodeUpdate);

      const draftResult = await ensureDraft({ skipDirtyCheck: true });

      if (draftResult === false) {
        if (prevData) updateNodeData(nodeId, prevData);
        return;
      }

      if (draftResult !== "created") {
        // Already a draft — fire individual PATCH
        try {
          await partialUpdate(nodeId, nodeUpdate);
        } catch {
          if (prevData) updateNodeData(nodeId, prevData);
          enqueueSnackbar("Failed to save agent node", { variant: "error" });
          return;
        }
      }

      queryClient.invalidateQueries({
        queryKey: ["agent-playground", "node-detail"],
      });
      clearSelectedNode();
    },
    (errors) => {
      logger.error("AgentNodeForm validation errors", errors);
    },
  );

  return {
    control,
    isPending,
    agentOptions,
    versionOptions,
    inputPorts,
    variableOptions,
    selectedGraphId,
    selectedVersionId,
    isLoadingGraphs,
    versionDetailData,
    handleAgentChange,
    handleVersionChange,
    onSubmit,
  };
}
