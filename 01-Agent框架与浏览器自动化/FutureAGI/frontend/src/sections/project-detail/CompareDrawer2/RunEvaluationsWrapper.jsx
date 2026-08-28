import React from "react";
import PropTypes from "prop-types";

import RunEvaluations from "./RunEvaluations";

const RunEvaluationsWrapper = React.memo(
  ({ traceData, selectedEvals, index }) => {
    return (
      <RunEvaluations
        traceData={traceData}
        selectedEvals={selectedEvals}
        index={index}
      />
    );
  },
);

RunEvaluationsWrapper.propTypes = {
  traceData: PropTypes.object,
  selectedEvals: PropTypes.object,
  index: PropTypes.number,
};

RunEvaluationsWrapper.displayName = "RunEvaluationsWrapper";

export default RunEvaluationsWrapper;
