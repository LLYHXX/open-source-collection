import React, { useState } from "react";
import PropTypes from "prop-types";

import { ProjectExperimentContext } from "./ProjectExperimentContext";

const ProjectExperimentContextProvider = ({ children }) => {
  const [projectExperimentSearch, setProjectExperimentSearch] = useState("");

  return (
    <ProjectExperimentContext.Provider
      value={{ projectExperimentSearch, setProjectExperimentSearch }}
    >
      {children}
    </ProjectExperimentContext.Provider>
  );
};

ProjectExperimentContextProvider.propTypes = {
  children: PropTypes.node,
};

export default ProjectExperimentContextProvider;
