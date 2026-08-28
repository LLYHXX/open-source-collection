/**
 * Shared tab styling for annotation views.
 * Used by AnnotationsTabs and queue-detail-view to keep styles in sync.
 */
export const getAnnotationTabSx = (theme) => ({
  minHeight: 42,
  fontSize: 14,
  "& .MuiTabs-flexContainer": {
    gap: 0,
  },
  mb: 2,
  "& .MuiTab-root": {
    minHeight: 42,
    paddingX: theme.spacing(1.5),
    margin: theme.spacing(0),
    marginRight: "0px !important",
    minWidth: "auto",
    fontWeight: "fontWeightMedium",
    typography: "body2",
    color: "text.disabled",
    textTransform: "none",
    transition: theme.transitions.create(["color", "background-color"], {
      duration: theme.transitions.duration.short,
    }),
    "&.Mui-selected": {
      color: "primary.main",
      fontWeight: "fontWeightSemiBold",
    },
    "&:not(.Mui-selected)": {
      color: theme.palette.text.secondary,
    },
  },
});

export const getAnnotationTabIndicatorProps = (theme) => ({
  style: {
    backgroundColor: theme.palette.primary.main,
  },
});
