import React from "react";
import PropTypes from "prop-types";
import { BaseStatusCellRenderer } from "src/sections/common/simulation";
import { useSimulationDetailContext } from "../context/SimulationDetailContext";

const ExecutionStatusCellRenderer = (params) => {
  const { refreshGrid } = useSimulationDetailContext();

  return (
    <BaseStatusCellRenderer
      params={params}
      onRefresh={refreshGrid}
      showSnackbar={true}
    />
  );
};

ExecutionStatusCellRenderer.propTypes = {
  params: PropTypes.object,
};

export default ExecutionStatusCellRenderer;
