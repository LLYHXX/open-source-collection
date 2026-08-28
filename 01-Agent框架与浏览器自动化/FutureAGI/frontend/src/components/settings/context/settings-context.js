import { useContext, createContext } from "react";

// ----------------------------------------------------------------------

export const SettingsContext = createContext({
  open: false,
  canReset: true,
  themeLayout: "vertical",
  themeStretch: false,
  themeContrast: "default",
  themeDirection: "ltr",
  themeMode: "system",
});

export const useSettingsContext = () => {
  const context = useContext(SettingsContext);

  if (!context)
    throw new Error("useSettingsContext must be use inside SettingsProvider");

  return context;
};
