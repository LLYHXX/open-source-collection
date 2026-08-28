import { loadingButtonClasses } from "@mui/lab/LoadingButton";

// ----------------------------------------------------------------------

export function loadingButton(theme) {
  const lightMode = theme.palette.mode === "light";

  return {
    MuiLoadingButton: {
      styleOverrides: {
        root: ({ ownerState }) => {
          const baseStyles = {};

          if (ownerState.variant === "soft") {
            Object.assign(baseStyles, {
              [`& .${loadingButtonClasses.loadingIndicatorStart}`]: {
                left: 10,
              },
              [`& .${loadingButtonClasses.loadingIndicatorEnd}`]: {
                right: 14,
              },
              ...(ownerState.size === "small" && {
                [`& .${loadingButtonClasses.loadingIndicatorStart}`]: {
                  left: 10,
                },
                [`& .${loadingButtonClasses.loadingIndicatorEnd}`]: {
                  right: 10,
                },
              }),
            });
          }

          if (ownerState.variant === "outlined") {
            Object.assign(baseStyles, {
              borderColor: lightMode
                ? theme.palette.whiteScale[500]
                : theme.palette.border.default,
              borderWidth: 1,
              [`& .${loadingButtonClasses.loadingIndicatorStart}`]: {
                left: 12,
              },
              [`& .${loadingButtonClasses.loadingIndicatorEnd}`]: {
                right: 12,
              },
              ...(ownerState.size === "small" && {
                [`& .${loadingButtonClasses.loadingIndicatorStart}`]: {
                  left: 8,
                },
                [`& .${loadingButtonClasses.loadingIndicatorEnd}`]: {
                  right: 8,
                },
              }),
              ...(ownerState.loading && {
                backgroundColor: lightMode
                  ? theme.palette.whiteScale[50]
                  : theme.palette.background.neutral,
                borderColor: theme.palette.action.disabled,
                color: "transparent !important",
              }),
              "&:hover": {
                borderColor: lightMode
                  ? theme.palette.black[200]
                  : theme.palette.border.hover,
                backgroundColor: lightMode
                  ? theme.palette.whiteScale[300]
                  : theme.palette.action.hover,
              },
              "&:disabled": {
                borderColor: lightMode
                  ? theme.palette.black[50]
                  : theme.palette.border.default,
                backgroundColor: lightMode
                  ? theme.palette.whiteScale[50]
                  : theme.palette.background.neutral,
                color: theme.palette.text.disabled,
              },
            });
          }

          return baseStyles;
        },
      },
    },
  };
}
