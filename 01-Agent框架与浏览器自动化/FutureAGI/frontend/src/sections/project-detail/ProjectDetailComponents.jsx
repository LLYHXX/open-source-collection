import { Button, styled } from "@mui/material";

export const OutlinedButton = styled(Button)(({ theme }) => ({
  // fontWeight: 'fontWeightRegular',
  // borderColor: 'divider',
  borderColor: theme.palette.divider,
  color: theme.palette.text.primary,
  "&:hover": {
    border: `1px solid ${theme.palette.divider} !important`,
    borderColor: theme.palette.divider,
    backgroundColor: theme.palette.background.neutral,
  },
  "& .MuiButton-startIcon, & .MuiButton-endIcon": {
    color: theme.palette.text.primary,
    height: theme.spacing(2),
    width: theme.spacing(2),
    "& .svg-color": {
      height: `${theme.spacing(2)} !important`,
      width: `${theme.spacing(2)} !important`,
      color: theme.palette.text.primary,
    },
    "& svg": {
      height: theme.spacing(2),
      width: theme.spacing(2),
    },
  },
}));
