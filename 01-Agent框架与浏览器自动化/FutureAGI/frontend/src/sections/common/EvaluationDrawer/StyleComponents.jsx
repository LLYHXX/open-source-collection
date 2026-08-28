import { styled } from "@mui/material/styles";
import Button from "@mui/material/Button";

export const EvalsButton = styled(Button)(({ theme }) => ({
  color: theme.palette.text.primary,
  backgroundColor: "transparent",
  border: "1px solid",
  fontSize: "12px",
  fontWeight: 400,
  px: 1,
  borderColor: theme.palette.divider,
  borderRadius: "4px",
  "&:hover": {
    backgroundColor: theme.palette.action.hover,
  },
  lineHeight: "16px",
}));
