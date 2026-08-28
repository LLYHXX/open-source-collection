import React, { useEffect, useRef, useState } from "react";
import DropdownWithSearch from "src/sections/common/DropdownWithSearch";
import AgentSelectDropDown from "./AgentSelectDropDown";
import { useAgentsList } from "../helper";
import { useNavigate, useParams } from "react-router";
import { Skeleton } from "@mui/material";
import { useAgentDetailsStore } from "../store/agentDetailsStore";

export const AgentDropdown = () => {
  const plusRef = useRef(null);
  const { agents, isLoading } = useAgentsList();
  const [selectedAgent, setSelectedAgent] = useState(null);
  const { agentDefinitionId } = useParams();
  const { setSelectedVersion } = useAgentDetailsStore();
  const navigate = useNavigate();
  useEffect(() => {
    if (agents?.length && agentDefinitionId) {
      const found = agents.find((a) => a.id === agentDefinitionId);
      if (found) setSelectedAgent(found);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agents]);

  const renderValue = (agent) => agent?.agent_name || "Select Agent";

  const fetchAgents = (searchText) => {
    if (!agents) return { data: [], isLoading: true, error: null };
    const filtered = agents.filter((agent) =>
      agent.agent_name.toLowerCase().includes(searchText.toLowerCase()),
    );
    return { data: filtered, isLoading: false, error: null };
  };
  const handleSelect = (agent) => {
    if (!agent?.id || !agent?.latest_version_id) return;

    // Update local state
    setSelectedAgent(agent);
    setSelectedVersion(agent?.latest_version_id);
    navigate(
      `/dashboard/simulate/agent-definitions/${agent.id}?version=${agent?.latest_version_id}`,
      {
        replace: true,
      },
    );
  };

  if (isLoading) {
    return (
      <Skeleton
        variant="rectangular"
        width={180}
        height={32}
        sx={{ borderRadius: 0 }}
      />
    );
  }

  return (
    <DropdownWithSearch
      value={selectedAgent}
      setValue={setSelectedAgent}
      options={[]}
      renderValue={renderValue}
      anchorRef={plusRef}
      ref={plusRef}
      popoverComponent={(props) => (
        <AgentSelectDropDown
          {...props}
          fetchOptions={fetchAgents}
          searchPlaceholder="Search Agent Definition"
          labelText="All Agents"
          onSelect={handleSelect}
          ref={plusRef}
        />
      )}
      sx={{ width: "fit-content" }}
      useCustomStyle
    />
  );
};
