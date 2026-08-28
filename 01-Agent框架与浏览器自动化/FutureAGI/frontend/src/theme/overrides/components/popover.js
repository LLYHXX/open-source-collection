import { listClasses } from "@mui/material/List";

import { paper } from "../../css";
import { darkElevatedStyles } from "../dark-elevated";

// ----------------------------------------------------------------------

export function popover(theme) {
  return {
    MuiPopover: {
      styleOverrides: {
        paper: {
          ...paper({ theme, dropdown: true }),
          ...darkElevatedStyles(theme),
          [`& .${listClasses.root}`]: {
            paddingTop: 0,
            paddingBottom: 0,
          },
        },
      },
    },
  };
}
