import { createContext, useContext } from "react";

// Create the context
export const DrawerContext = createContext({
  gridApi: null,
});

// Custom hook to use the drawer context
export const useReplayDrawerContext = () => {
  const context = useContext(DrawerContext);
  if (!context) {
    throw new Error("useDrawerContext must be used within DrawerProvider");
  }
  return context;
};
