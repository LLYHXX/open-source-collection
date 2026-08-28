import { Chip, styled } from "@mui/material";

export const AGIChip = styled(Chip)(({ theme }) => ({
  backgroundColor: theme.palette.action.hover,
  color: theme.palette.primary.main,
  borderRadius: "4px",
  fontWeight: 500,
  fontSize: "12px",
  "&:hover": {
    backgroundColor: theme.palette.action.selected,
    borderColor: theme.palette.action.selected,
  },
}));
