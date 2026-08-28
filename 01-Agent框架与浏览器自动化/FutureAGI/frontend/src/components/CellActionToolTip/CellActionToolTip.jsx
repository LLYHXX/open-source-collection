import { Tooltip, styled, tooltipClasses } from "@mui/material";

const CellActionToolTip = styled(({ className, ...props }) => (
  <Tooltip {...props} classes={{ popper: className }} />
))(() => ({
  [`& .${tooltipClasses.tooltip}`]: {
    padding: 0,
    margin: 0,
    minWidth: 0,
    maxWidth: "none",
    width: "auto",
    height: "auto",
    background: "transparent",
    backgroundColor: "transparent",
    boxShadow: "none",
    border: "none",
    borderRadius: 0,
    lineHeight: 0,
    overflow: "visible",
    transition: "all 0.2s ease-in-out",
    marginLeft: "-44px !important",
    cursor: "pointer",
  },
}));

export default CellActionToolTip;
