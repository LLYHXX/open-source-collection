import { createContext, useContext } from "react";

export const ProjectExperimentContext = createContext({
  projectExperimentSearch: "",
  setProjectExperimentSearch: () => {},
});

export const useProjectExperimentContext = () => {
  return useContext(ProjectExperimentContext);
};
