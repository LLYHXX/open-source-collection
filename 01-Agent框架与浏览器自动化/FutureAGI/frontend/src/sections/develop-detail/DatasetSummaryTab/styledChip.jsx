import { Chip, styled } from "@mui/material";

const StyledChip = styled(Chip)(({ theme }) => ({
  borderRadius: "4px",
  border: "1px solid",
  borderColor: theme.palette.primary.lighter,
  backgroundColor: theme.palette.action.hover,
  color: theme.palette.primary.main,
  "&:hover": {
    backgroundColor: theme.palette.action.selected,
    color: theme.palette.primary.main,
  },
  "& .MuiChip-deleteIcon": {
    color: theme.palette.primary.main,
    opacity: 1,
    "&:hover": {
      opacity: 0.5,
      color: theme.palette.primary.main,
    },
  },
}));

export default StyledChip;
