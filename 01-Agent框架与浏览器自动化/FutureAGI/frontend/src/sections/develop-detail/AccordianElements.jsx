import React from "react";
import {
  Accordion as MuiAccordion,
  AccordionSummary as MuiAccordionSummary,
  AccordionDetails as MuiAccordionDetails,
  styled,
} from "@mui/material";
import Iconify from "src/components/iconify";

export const Accordion = styled((props) => (
  <MuiAccordion disableGutters elevation={0} square {...props} />
))(({ theme }) => ({
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: "10px",
  "&::before": {
    display: "none",
  },
  "&.Mui-expanded": {
    boxShadow: "none",
  },
}));

export const AccordionSummary = styled((props) => (
  <MuiAccordionSummary
    expandIcon={
      <Iconify
        icon="material-symbols:arrow-forward-ios-rounded"
        sx={{ color: "text.secondary" }}
        width={16}
      />
    }
    {...props}
  />
))(({ theme }) => ({
  backgroundColor: theme.palette.background.paper,
  borderRadius: "10px",
  flexDirection: "row-reverse",
  fontWeight: 500,
  fontSize: "14px",
  color: "text.primary",
  "& .MuiAccordionSummary-expandIconWrapper.Mui-expanded": {
    transform: "rotate(90deg)",
  },
  "& .MuiAccordionSummary-content": {
    marginLeft: theme.spacing(1),
  },
}));

export const AccordionDetails = styled((props) => (
  <MuiAccordionDetails {...props} />
))(({ theme }) => ({
  paddingX: theme.spacing(1),
  paddingY: 0,
}));
