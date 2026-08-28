import React from "react";
import PropTypes from "prop-types";
import { BaseStatusCellRenderer } from "src/sections/common/simulation";
import { useTestDetailContext } from "../../context/TestDetailContext";

const TestStatusCellRenderer = (params) => {
  const { refreshTestRunGrid } = useTestDetailContext();

  return (
    <BaseStatusCellRenderer
      params={params}
      onRefresh={refreshTestRunGrid}
      showSnackbar={false}
    />
  );
};

TestStatusCellRenderer.propTypes = {
  params: PropTypes.object.isRequired,
};

export default TestStatusCellRenderer;
