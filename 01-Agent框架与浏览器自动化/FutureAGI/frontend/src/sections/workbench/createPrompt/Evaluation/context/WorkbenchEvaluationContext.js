import { createContext, useContext } from "react";

export const WorkbenchEvaluationContext = createContext({
  versions: [],
  setVersions: (_value) => {},
  variables: {},
  setVariables: (_value) => {},
  compareOpen: false,
  setCompareOpen: (_value) => {},
  isEvaluationDrawerOpen: false,
  setIsEvaluationDrawerOpen: (_value) => {},
  showPrompts: false,
  setShowPrompts: (_value) => {},
  showVariables: true,
  setShowVariables: (_value) => {},
  isEvalsCompareOpen: false,
  setIsEvalsCompareOpen: (_value) => {},
});

export const useWorkbenchEvaluationContext = () => {
  return useContext(WorkbenchEvaluationContext);
};
