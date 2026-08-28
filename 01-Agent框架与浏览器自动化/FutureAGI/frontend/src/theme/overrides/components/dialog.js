import { darkElevatedStyles } from "../dark-elevated";

// ----------------------------------------------------------------------

export function dialog(theme) {
  return {
    MuiDialog: {
      styleOverrides: {
        paper: ({ ownerState }) => ({
          boxShadow: theme.customShadows.dialog,
          borderRadius: theme.shape.borderRadius * 2,
          ...darkElevatedStyles(theme, {
            boxShadow: "0px 24px 64px -8px rgba(0, 0, 0, 0.8)",
          }),
          ...(!ownerState.fullScreen && {
            margin: theme.spacing(2),
          }),
        }),
        paperFullScreen: {
          borderRadius: 0,
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          padding: theme.spacing(3),
        },
      },
    },
    MuiDialogContent: {
      styleOverrides: {
        root: {
          padding: theme.spacing(0, 3),
        },
        dividers: {
          borderTop: 0,
          borderBottomStyle: "dashed",
          paddingBottom: theme.spacing(3),
        },
      },
    },
    MuiDialogActions: {
      styleOverrides: {
        root: {
          padding: theme.spacing(3),
          "& > :not(:first-of-type)": {
            marginLeft: theme.spacing(1.5),
          },
        },
      },
    },
  };
}
