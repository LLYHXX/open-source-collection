import { createContext, useContext } from "react";

export const EvaluationContext = createContext({
  module: "dataset",
  isDirty: false,
  selectedEval: {},
  visibleSection: "list",
  selectedColumn: "",
  actionButtonConfig: {
    id: "",
    showTest: true,
    showAdd: true,
    runLabel: "Add & Run",
    testLabel: "Test",
    handleRun: (_data, _onSuccess, _meta, _setVisibleSection) => {},
    handleTest: (_data) => {},
    showDefaultButton: true,
  },
  setModule: (_value) => {},
  setIsDirty: (_value) => {},
  setVisibleSection: (_value) => {},
  setSelectedColumn: (_value) => {},
  setSelectedEval: (_value) => {},
  setActionButtonConfig: (_value) => {},
  setFormValues: (_value) => {},
  formValues: {},
  setPlaygroundEvaluation: (_value) => {},
  playgroundEvaluation: null,
  viewEvalsDetails: null,
  setViewEvalsDetails: (_value) => {},
  currentTab: "evals",
  setCurrentTab: (_tba) => {},
  selectedGroup: null,
  setSelectedGroup: (_id) => {},
  openEditForSavedEval: null,
  registerOpenEditForSavedEval: (_fn) => {},
});

export const useEvaluationContext = () => {
  return useContext(EvaluationContext);
};
