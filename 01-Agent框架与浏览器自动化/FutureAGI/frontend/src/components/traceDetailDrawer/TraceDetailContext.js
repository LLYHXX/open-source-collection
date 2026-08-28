import React from "react";

export const TraceDetailContext = React.createContext({
  configureAnnotationsDrawerOpen: false,
  setConfigureAnnotationsDrawerOpen: () => {},
  addLabelDrawerOpen: false,
  setAddLabelDrawerOpen: () => {},
});

export const useTraceDetailContext = () => {
  return React.useContext(TraceDetailContext);
};
