import { Box, styled, Tab, tabClasses, Tabs } from "@mui/material";
import { typography } from "src/theme/typography";

export const TabWrapper = styled(Box)(({ theme }) => ({
  display: "inline-flex",
  border: `1px solid ${theme.palette.divider}`,
  padding: theme.spacing(0.5),
  borderRadius: theme.spacing(1),
  backgroundColor: theme.palette.background.paper,
}));

export const CustomTabs = styled(Tabs)(({ theme }) => ({
  minHeight: "auto",
  "& .MuiTabs-indicator": {
    backgroundColor: theme.palette.action.hover,
    borderRadius: theme.spacing(0.5),
    height: "100%",
    zIndex: 0,
  },
}));

export const CustomTab = styled(Tab)(({ theme }) => ({
  fontFamily: typography.fontFamily,
  paddingLeft: theme.spacing(1.5),
  paddingRight: theme.spacing(1.5),
  minHeight: "auto",
  height: "auto",
  paddingTop: theme.spacing(0.75),
  paddingBottom: theme.spacing(0.75),
  ...typography.s2,
  fontWeight: typography.fontWeightSemiBold,
  textTransform: "none",
  borderRadius: theme.spacing(0.5),
  marginRight: "2px !important",
  color: theme.palette.text.disabled,
  backgroundColor: "transparent",
  position: "relative",
  zIndex: 1,
  transition: theme.transitions.create(["color"], {
    duration: theme.transitions.duration.short,
  }),
  [`&:not(.${tabClasses.selected})`]: {
    color: theme.palette.text.disabled,
    fontWeight: typography.fontWeightMedium,
  },
  [`&.${tabClasses.selected}`]: {
    color: theme.palette.primary.main,
    fontWeight: typography.fontWeightSemiBold,
  },
  "&:last-of-type": {
    marginRight: 0,
  },
}));
