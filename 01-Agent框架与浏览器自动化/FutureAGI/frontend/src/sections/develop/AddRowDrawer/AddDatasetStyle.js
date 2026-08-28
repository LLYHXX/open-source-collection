import { Box, styled, Tab, tabClasses, Tabs } from "@mui/material";
import { typography } from "src/theme/typography";

export const TabWrapper = styled(Box)(({ theme }) => ({
  display: "inline-flex",
  border: `1px solid ${theme.palette.background.neutral}`,
  padding: "4px",
  borderRadius: "8px",
  marginBottom: "12px",
}));
export const CustomTabs = styled(Tabs)(() => ({
  minHeight: "22px",
}));
export const CustomTab = styled(Tab)(({ theme }) => ({
  fontFamily: typography.fontFamily,
  paddingLeft: "12px",
  paddingRight: "12px",
  minHeight: "22px",
  ...typography.subtitle2,
  ["&:not(:last-of-type)"]: {
    marginRight: "4px",
  },
  [`&:not(.${tabClasses.selected})`]: {
    color: theme.palette.text.secondary,
  },
  ...theme.typography["s1"],
  fontWeight: theme.typography["fontWeightRegular"],
}));
