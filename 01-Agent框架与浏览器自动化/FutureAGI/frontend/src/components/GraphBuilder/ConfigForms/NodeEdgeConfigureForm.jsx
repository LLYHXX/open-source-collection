import React from "react";
import { useGraphStore } from "../store/graphStore";
import { Drawer } from "@mui/material";
import ConfigureEdgeForm from "./ConfigureEdgeForm";
import ConfigureNodeForm from "./ConfigureNodeForm";

const NodeEdgeConfigureForm = () => {
  const activeEdgeId = useGraphStore((state) => state.activeEdgeId);
  const activeNodeId = useGraphStore((state) => state.activeNodeId);
  const updateEdgeData = useGraphStore((state) => state.updateEdgeData);
  const updateNode = useGraphStore((state) => state.updateNode);
  const edges = useGraphStore((state) => state.edges);
  const nodes = useGraphStore((state) => state.nodes);

  const onCloseHandler = () => {
    useGraphStore.getState().setActiveEdge(null);
    useGraphStore.getState().setActiveNode(null);
  };

  // if (!activeEdgeId && !activeNodeId) {
  //   return null;
  // }

  const renderForm = () => {
    if (activeEdgeId) {
      const activeEdge = edges.find((edge) => edge.id === activeEdgeId);
      return (
        <ConfigureEdgeForm
          edge={activeEdge}
          onChange={updateEdgeData}
          onClose={onCloseHandler}
        />
      );
    }
    if (activeNodeId) {
      const activeNode = nodes.find((node) => node.id === activeNodeId);
      return (
        <ConfigureNodeForm
          node={activeNode}
          onChange={updateNode}
          onClose={onCloseHandler}
        />
      );
    }
  };

  return (
    <Drawer
      anchor="right"
      open={activeEdgeId || activeNodeId}
      onClose={onCloseHandler}
      variant="persistent"
      sx={{
        "& .MuiDrawer-paper": {
          width: "483px",
          boxSizing: "border-box",
        },
      }}
    >
      {renderForm()}
    </Drawer>
  );
};

export default NodeEdgeConfigureForm;
