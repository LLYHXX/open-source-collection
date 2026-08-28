import { createContext, useContext } from "react";

export const DevelopDetailContext = createContext({
  diffMode: false,
  handleToggleDiffMode: () => {},
  getActionSource: () => null,
  setActionSource: () => {},
  clearActionSource: () => {},
});

export const useDevelopDetailContext = () => {
  return useContext(DevelopDetailContext);
};
