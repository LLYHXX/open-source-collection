import { menuItem } from "../../css";
import { darkElevatedStyles } from "../dark-elevated";

// ----------------------------------------------------------------------

export function menu(theme) {
  return {
    MuiMenu: {
      styleOverrides: {
        paper: {
          ...darkElevatedStyles(theme),
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          ...menuItem(theme),
        },
      },
    },
  };
}
