import React from "react";
import PropTypes from "prop-types";

import RunAnnotations from "./RunAnnotations";

const RunAnnotationsWrapper = React.memo(({ traceData }) => {
  return <RunAnnotations traceData={traceData} />;
});

RunAnnotationsWrapper.propTypes = {
  traceData: PropTypes.object,
};

RunAnnotationsWrapper.displayName = "RunAnnotationsWrapper";

export default RunAnnotationsWrapper;
