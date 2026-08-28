import React, { useState } from "react";
import PropTypes from "prop-types";

import { ProjectObserveContext } from "./ProjectObserveContext";

const ProjectObserveContextProvider = ({ children }) => {
  const [projectObserveSearch, setProjectObserveSearch] = useState("");

  return (
    <ProjectObserveContext.Provider
      value={{ projectObserveSearch, setProjectObserveSearch }}
    >
      {children}
    </ProjectObserveContext.Provider>
  );
};

ProjectObserveContextProvider.propTypes = {
  children: PropTypes.node,
};

export default ProjectObserveContextProvider;
