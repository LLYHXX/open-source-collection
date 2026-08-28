import { darkElevatedStyles } from "../dark-elevated";

// ----------------------------------------------------------------------

export function tooltip(theme) {
  const lightMode = theme.palette.mode === "light";

  return {
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: theme.palette.grey[lightMode ? 800 : 700],
          ...darkElevatedStyles(theme, { borderOnly: true }),
        },
        arrow: {
          color: theme.palette.grey[lightMode ? 800 : 700],
        },
      },
    },
  };
}
