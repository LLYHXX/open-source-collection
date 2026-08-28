import React from "react";
import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import LoadingButton from "@mui/lab/LoadingButton";
import AgentGraphPreview from "../../../components/AgentGraphPreview";
import { FormSearchSelectFieldControl } from "src/components/FromSearchSelectField";
import AgentNodeFormSkeleton from "./AgentNodeFormSkeleton";
import InputMappingRow from "./InputMappingRow";
import { useAgentNodeForm } from "./useAgentNodeForm";

export default function AgentNodeForm({ nodeId }) {
  const {
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
  } = useAgentNodeForm(nodeId);

  if (isLoadingGraphs) return <AgentNodeFormSkeleton />;

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 1.5,
        height: "100%",
      }}
    >
      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          gap: 2,
        }}
      >
        {/* Agent Graph Dropdown */}
        <Box sx={{ pt: 0.5 }}>
          <FormSearchSelectFieldControl
            control={control}
            fieldName="graphId"
            label="Agent"
            fullWidth
            placeholder="Select agent"
            size="small"
            options={agentOptions}
            required
            onChange={handleAgentChange}
            rules={{ required: "Agent is required" }}
          />
        </Box>

        {/* Version dropdown — fetched from API, active/inactive only */}
        <Box>
          <FormSearchSelectFieldControl
            control={control}
            fieldName="versionId"
            label="Version"
            fullWidth
            placeholder={
              selectedGraphId ? "Select version" : "Select an agent first"
            }
            size="small"
            options={versionOptions}
            required
            onChange={handleVersionChange}
            rules={{ required: "Version is required" }}
          />
        </Box>

        {/* Graph Preview - shown when both agent and version are selected */}
        <AgentGraphPreview
          agentId={selectedGraphId}
          versionId={selectedVersionId}
          versionData={versionDetailData}
        />

        {/* Input Port Mapping */}
        {inputPorts.length > 0 && (
          <Box
            sx={{
              border: "1px solid",
              borderColor: "divider",
              borderRadius: "4px",
              p: 2,
              display: "flex",
              flexDirection: "column",
              gap: 1.5,
            }}
          >
            <Typography
              variant="caption"
              fontWeight="fontWeightBold"
              color="text.secondary"
              sx={{ textTransform: "capitalize", letterSpacing: 0.5 }}
            >
              Input Mapping
            </Typography>
            {inputPorts.map((port, index) => (
              <InputMappingRow
                key={port.id}
                port={port}
                index={index}
                control={control}
                variableOptions={variableOptions}
              />
            ))}
          </Box>
        )}
      </Box>

      {/* Save Button - bottom right */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-end",
          pt: 1.5,
          borderTop: 1,
          borderColor: "divider",
        }}
      >
        <LoadingButton
          type="button"
          size="small"
          variant="outlined"
          loading={isPending}
          onClick={onSubmit}
        >
          Save
        </LoadingButton>
      </Box>
    </Box>
  );
}

AgentNodeForm.propTypes = {
  nodeId: PropTypes.string.isRequired,
};
