import { createContext, useContext } from "react";

export const TestDetailContext = createContext({
  setTestRunGridApi: () => {},
  getTestRunGridApi: () => {},
  refreshTestRunGrid: () => {},
  testData: null,
  isTestDataPending: false,
  executionsCount: null,
});

export const useTestDetailContext = () => {
  return useContext(TestDetailContext);
};
