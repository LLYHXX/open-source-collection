/** Shared sx for outlined "Back" buttons with left arrow icon */
export const backButtonSx = {
  color: "text.primary",
  borderColor: "action.hover",
  typography: "s1",
  fontWeight: "fontWeightMedium",
  "&:hover": { borderColor: "text.disabled" },
  "& .MuiButton-startIcon": { marginRight: "4px" },
};

/** Shared sx for outlined neutral buttons (Cancel, secondary actions) */
export const outlinedNeutralButtonSx = {
  color: "text.primary",
  borderColor: "action.hover",
  fontWeight: 500,
  "&:hover": { borderColor: "text.disabled" },
};
