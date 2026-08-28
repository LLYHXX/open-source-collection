import { createContext, useContext } from "react";

export const DevelopDetailContext = createContext({
  gridApi: null,
  setGridApi: () => {},
  refreshGrid: () => {},
  setRefetchTable: (_func) => {},
});

export const useDevelopDetailContext = () => {
  const context = useContext(DevelopDetailContext);
  if (!context) {
    throw new Error(
      "useDevelopDetailContext must be used within a DevelopDetailProvider",
    );
  }
  return context;
};
