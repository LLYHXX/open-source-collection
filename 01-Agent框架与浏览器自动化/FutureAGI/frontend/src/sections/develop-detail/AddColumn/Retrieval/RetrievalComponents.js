import { styled, Box } from "@mui/material";

export const RetrievalFormItemWrapper = styled(Box)(({ theme }) => ({
  paddingLeft: theme.spacing(2),
  paddingRight: theme.spacing(2),
  paddingTop: theme.spacing(3),
  paddingBottom: theme.spacing(3),
  borderBottom: `2px solid ${theme.palette.background.neutral}`,
}));
