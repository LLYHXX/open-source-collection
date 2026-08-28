import { alpha } from "@mui/material/styles";

// ----------------------------------------------------------------------

export function paper(theme) {
  return {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
        },
        outlined: {
          borderColor:
            theme.palette.border?.default ||
            alpha(theme.palette.grey[500], 0.16),
        },
      },
    },
  };
}
