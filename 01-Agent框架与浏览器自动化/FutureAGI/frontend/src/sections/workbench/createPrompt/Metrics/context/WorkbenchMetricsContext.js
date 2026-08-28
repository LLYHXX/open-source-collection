import { createContext, useContext } from "react";

export const WorkbenchMetricsContext = createContext(null);

export const useWorkbenchMetrics = () => {
  const context = useContext(WorkbenchMetricsContext);
  if (!context) {
    throw new Error(
      "useWorkbenchMetrics must be used within a WorkbenchMetricsProvider",
    );
  }
  return context;
};
