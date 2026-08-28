// ----------------------------------------------------------------------

export function radio(theme) {
  const lightMode = theme.palette.mode === "light";

  return {
    // CHECKBOX, RADIO, SWITCH
    MuiFormControlLabel: {
      styleOverrides: {
        label: {
          ...theme.typography.body2,
        },
      },
    },

    MuiRadio: {
      styleOverrides: {
        root: {
          padding: theme.spacing(1),
          color: lightMode
            ? theme.palette.black?.o20
            : theme.palette.grey?.[600],
          "&.Mui-checked": {
            color: theme.palette.purple?.[300],
          },
        },
      },
    },
  };
}
