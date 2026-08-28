import { alpha } from "@mui/material/styles";
import { drawerClasses } from "@mui/material/Drawer";

import { paper } from "../../css";

// ----------------------------------------------------------------------

export function drawer(theme) {
  const lightMode = theme.palette.mode === "light";
  const darkBorder = theme.palette.border?.hover || "#3f3f46";

  return {
    MuiDrawer: {
      styleOverrides: {
        root: ({ ownerState }) => ({
          ...(ownerState.variant === "temporary" && {
            [`& .${drawerClasses.paper}`]: {
              ...paper({ theme }),
              ...(!lightMode && {
                backgroundColor: theme.palette.background.neutral,
                borderLeft: `1px solid ${darkBorder}`,
                borderRight: `1px solid ${darkBorder}`,
              }),
              ...(ownerState.anchor === "left" && {
                boxShadow: lightMode
                  ? `40px 40px 80px -8px ${alpha(theme.palette.grey[500], 0.24)}`
                  : `8px 0px 40px 0px rgba(0, 0, 0, 0.7)`,
              }),
              ...(ownerState.anchor === "right" && {
                boxShadow: lightMode
                  ? `-40px 40px 80px -8px ${alpha(theme.palette.grey[500], 0.24)}`
                  : `-8px 0px 40px 0px rgba(0, 0, 0, 0.7)`,
              }),
            },
          }),
        }),
      },
    },
  };
}
