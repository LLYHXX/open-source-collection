import { createContext, useContext } from "react";

export const TestDetailContext = createContext({
  refreshGrid: () => {},
  setGridApi: () => {},
  getGridApi: () => {},
  refreshOptimizationGrid: () => {},
  setOptimizationGridApi: () => {},
  getOptimizationGridApi: () => {},
});

export const useTestDetail = () => {
  const context = useContext(TestDetailContext);
  if (!context) {
    throw new Error("useTestDetail must be used within TestDetailProvider");
  }
  return context;
};
