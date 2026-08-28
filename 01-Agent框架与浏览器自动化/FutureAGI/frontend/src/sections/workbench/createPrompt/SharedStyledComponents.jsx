import { alpha, styled, Typography } from "@mui/material";

export const DraftBadge = styled(Typography)(({ theme }) => ({
  backgroundColor: alpha(theme.palette.warning.main, 0.12),
  borderRadius: "2px",
  color: theme.palette.warning.dark,
  paddingLeft: "6px",
  paddingRight: "6px",
  paddingTop: "4px",
  paddingBottom: "3px",
  fontSize: "11px",
  lineHeight: "16px",
  fontWeight: 500,
}));
