import React from "react";
import PropTypes from "prop-types";

import RunDetails from "./RunDetails";

const RunDetailsWrapper = React.memo(({ traceData }) => {
  return <RunDetails traceData={traceData} />;
});

RunDetailsWrapper.propTypes = {
  traceData: PropTypes.object,
};

RunDetailsWrapper.displayName = "RunDetailsWrapper";

export default RunDetailsWrapper;
