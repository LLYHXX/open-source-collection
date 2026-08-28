import { Checkbox, checkboxClasses, styled } from "@mui/material";

const SecondaryCheckbox = styled(Checkbox)(({ theme }) => ({
  color: theme.palette.text.disabled,
  [`&.${checkboxClasses.checked}`]: {
    color: theme.palette.secondary.light,
  },
}));

export default SecondaryCheckbox;
