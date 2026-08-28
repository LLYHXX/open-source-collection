import { Button, styled } from "@mui/material";

export const AddMessageButton = styled(Button)(({ theme }) => ({
  fontWeight: theme.typography.fontWeightMedium,
  ...(theme.typography.s1 || {}),
  padding: theme.spacing(0.75, 3),
  height: "38px",
  borderRadius: theme.spacing(1),
  minWidth: "152px",
  borderColor: theme.palette.divider,
}));
