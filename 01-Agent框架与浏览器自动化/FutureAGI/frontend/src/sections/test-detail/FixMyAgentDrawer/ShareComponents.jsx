import { Accordion, AccordionSummary, styled } from "@mui/material";

export const SuggestionAccordion = styled(Accordion)(({ theme }) => ({
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.spacing(1.5),
  boxShadow: "none",
  background: "var(--bg-neutral)",
  overflow: "hidden",
  margin: 0,
  "&::before": {
    display: "none",
  },
  "&.Mui-expanded": {
    margin: 0,
  },
}));

export const SuggestionAccordionSummary = styled(AccordionSummary)(
  ({ theme }) => ({
    backgroundColor: theme.palette.background.default,
    padding: theme.spacing(2),
    paddingBottom: "12px",
    minHeight: "auto",
    "& .MuiAccordionSummary-content": {
      margin: 0,
      "&.Mui-expanded": {
        margin: 0,
      },
    },
    "& .MuiAccordionSummary-expandIconWrapper": {
      color: theme.palette.text.disabled,
    },
  }),
);

export const SuggestionAccordionDetails = styled(AccordionSummary)(
  ({ theme }) => ({
    backgroundColor: theme.palette.background.default,
    padding: theme.spacing(2),
    paddingTop: 0,
    cursor: "default !important",

    "& .MuiAccordionSummary-content": {
      margin: "0px !important",
    },
  }),
);
