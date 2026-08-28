import PropTypes from "prop-types";
import React, { useState } from "react";

import { PromptContext } from "./prompt-context";

const PromptContextProvider = ({ children }) => {
  const [responseState, setResponseState] = useState([]);
  return (
    <PromptContext.Provider
      value={{
        responseState: responseState,
        setResponseState: setResponseState,
      }}
    >
      {children}
    </PromptContext.Provider>
  );
};

export default PromptContextProvider;

PromptContextProvider.propTypes = {
  children: PropTypes.node.isRequired,
  id: PropTypes.string.isRequired,
};
