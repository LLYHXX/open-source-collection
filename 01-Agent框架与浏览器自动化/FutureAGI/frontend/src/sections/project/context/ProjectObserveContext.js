import { createContext, useContext } from "react";

export const ProjectObserveContext = createContext({
  projectObserveSearch: "",
  setProjectObserveSearch: () => {},
});

export const useProjectObserveContext = () => {
  return useContext(ProjectObserveContext);
};
