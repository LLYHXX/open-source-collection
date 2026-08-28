import { styled, Tabs } from "@mui/material";

export const CustomTabs = styled(Tabs)(({ theme }) => ({
  "& .MuiTab-root": {
    color: theme.palette.text.disabled,
    ...theme.typography.s2,
    fontWeight: 500,
    "&.Mui-selected": {
      color: theme.palette.primary.main,
      fontWeight: 600,
    },
  },
  "& .MuiTabs-indicator": {
    backgroundColor: theme.palette.primary.main,
  },
}));
