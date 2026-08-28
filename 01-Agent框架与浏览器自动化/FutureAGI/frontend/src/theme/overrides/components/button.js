import { alpha } from "@mui/material/styles";
import { buttonClasses } from "@mui/material/Button";

// ----------------------------------------------------------------------

const COLORS = ["primary", "secondary", "info", "success", "warning", "error"];

// ----------------------------------------------------------------------

export function button(theme) {
  const lightMode = theme.palette.mode === "light";

  const rootStyles = (ownerState) => {
    const inheritColor = ownerState.color === "inherit";

    const containedVariant = ownerState.variant === "contained";

    const outlinedVariant = ownerState.variant === "outlined";

    const textVariant = ownerState.variant === "text";

    const softVariant = ownerState.variant === "soft";

    const smallSize = ownerState.size === "small";

    const mediumSize = ownerState.size === "medium";

    const largeSize = ownerState.size === "large";

    const defaultStyle = {
      borderRadius: theme.spacing(0.5),
      ...(inheritColor && {
        // CONTAINED
        ...(containedVariant && {
          color: lightMode
            ? theme.palette.common.white
            : theme.palette.grey[800],
          backgroundColor: lightMode
            ? theme.palette.grey[800]
            : theme.palette.common.white,
          "&:hover": {
            backgroundColor: lightMode
              ? theme.palette.grey[700]
              : theme.palette.grey[400],
          },
        }),
        // OUTLINED
        ...(outlinedVariant && {
          borderColor: lightMode
            ? theme.palette.whiteScale[500]
            : theme.palette.border.default,
          color: lightMode
            ? theme.palette.black[1000]
            : theme.palette.text.primary,
          "&:hover": {
            border: `1px solid ${lightMode ? theme.palette.black[200] : theme.palette.border.hover} !important`,
            borderColor: lightMode
              ? theme.palette.black[200]
              : theme.palette.border.hover,
            backgroundColor: lightMode
              ? theme.palette.whiteScale[300]
              : theme.palette.action.hover,
          },
          "& .MuiButton-startIcon, & .MuiButton-endIcon": {
            color: lightMode
              ? theme.palette.black[1000]
              : theme.palette.text.primary,
            "& .svg-color": {
              color: lightMode
                ? theme.palette.black[1000]
                : theme.palette.text.primary,
            },
          },
          "&.Mui-disabled": {
            borderColor: lightMode
              ? theme.palette.black[50]
              : theme.palette.border.default,
            backgroundColor: lightMode
              ? theme.palette.whiteScale[50]
              : theme.palette.background.neutral,
            color: lightMode
              ? theme.palette.black[100]
              : theme.palette.text.disabled,
            "& .MuiButton-startIcon, & .MuiButton-endIcon": {
              color: lightMode
                ? theme.palette.black[100]
                : theme.palette.text.disabled,
              "& .svg-color, & svg": {
                color: lightMode
                  ? theme.palette.black[100]
                  : theme.palette.text.disabled,
              },
            },
          },
        }),
        // TEXT
        ...(textVariant && {
          "&:hover": {
            backgroundColor: theme.palette.action.hover,
          },
        }),
        // SOFT
        ...(softVariant && {
          color: theme.palette.text.primary,
          backgroundColor: alpha(theme.palette.grey[500], 0.08),
          "&:hover": {
            backgroundColor: alpha(theme.palette.grey[500], 0.24),
          },
        }),
      }),
      // ...(outlinedVariant && {
      //   "&:hover": {
      //     borderColor: "currentColor",
      //     boxShadow: "0 0 0 0.5px currentColor",
      //   },
      // }),
      "& .MuiButton-startIcon, & .MuiButton-endIcon": {
        // height: theme.spacing(2),
        // width: theme.spacing(2),
        "& .svg-color": {
          height: `${theme.spacing(2)}`,
          width: `${theme.spacing(2)}`,
        },
        "& svg": {
          height: theme.spacing(2),
          width: theme.spacing(2),
        },
      },
      "&.Mui-disabled": {
        "& .MuiButton-startIcon, & .MuiButton-endIcon": {
          color: theme.palette.action.disabled,
          "& .svg-color, & svg": {
            color: theme.palette.action.disabled,
          },
        },
      },
    };

    const colorStyle = COLORS.map((color) => ({
      ...(ownerState.color === color && {
        // CONTAINED
        ...(containedVariant && {
          "&:hover": {
            boxShadow: theme.customShadows[color],
          },
        }),
        // SOFT
        ...(softVariant && {
          color: theme.palette[color][lightMode ? "dark" : "light"],
          backgroundColor: alpha(theme.palette[color].main, 0.16),
          "&:hover": {
            backgroundColor: alpha(theme.palette[color].main, 0.32),
          },
        }),
      }),
    }));

    const disabledState = {
      [`&.${buttonClasses.disabled}`]: {
        // SOFT
        ...(softVariant && {
          backgroundColor: theme.palette.action.disabledBackground,
        }),
      },
    };

    const size = {
      ...(smallSize && {
        height: 30,
        fontSize: 12,
        paddingLeft: 24,
        paddingRight: 24,
        paddingTop: 6,
        paddingBottom: 6,
        fontWeight: 500,
        ...(textVariant && {
          paddingLeft: 4,
          paddingRight: 4,
        }),
      }),
      ...(mediumSize && {
        paddingLeft: 24,
        paddingRight: 24,
        paddingTop: 8,
        paddingBottom: 8,
        fontSize: 14,
        height: 38,
        fontWeight: 500,
        ...(textVariant && {
          paddingLeft: 8,
          paddingRight: 8,
        }),
      }),
      ...(largeSize && {
        height: 48,
        fontSize: 15,
        paddingLeft: 16,
        paddingRight: 16,
        ...(textVariant && {
          paddingLeft: 10,
          paddingRight: 10,
        }),
      }),
    };

    return [defaultStyle, ...colorStyle, disabledState, size];
  };

  return {
    MuiButton: {
      styleOverrides: {
        root: ({ ownerState }) => rootStyles(ownerState),
      },
    },
  };
}
