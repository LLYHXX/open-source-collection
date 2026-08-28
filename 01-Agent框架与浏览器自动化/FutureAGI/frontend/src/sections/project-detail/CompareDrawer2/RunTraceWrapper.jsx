import React from "react";
import PropTypes from "prop-types";

import RunTrace from "./RunTrace";

const RunTraceWrapper = React.memo(({ traceData }) => {
  return <RunTrace traceData={traceData} />;
});

RunTraceWrapper.propTypes = {
  traceData: PropTypes.object,
  selectedEvals: PropTypes.object,
  totalRuns: PropTypes.number,
  index: PropTypes.number,
};

RunTraceWrapper.displayName = "RunTraceWrapper";

export default RunTraceWrapper;
