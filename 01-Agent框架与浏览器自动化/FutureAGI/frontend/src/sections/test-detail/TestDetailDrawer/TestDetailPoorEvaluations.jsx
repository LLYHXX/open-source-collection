import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Chip,
  Typography,
} from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import Iconify from "src/components/iconify";

const ChipForPoorEval = ({ label }) => {
  return (
    <Chip
      label={`${label}`}
      size="medium"
      sx={{
        typography: "s2",
        fontWeight: "fontWeightMedium",
        border: "1px solid",
        borderColor: "red.500",
        backgroundColor: "red.o5",
        color: "red.500",
        borderRadius: 0.5,
        px: 0.75,
        py: 0.75,
        "&:hover": {
          backgroundColor: "red.o5",
        },
        "& .MuiChip-deleteIcon": {
          color: "red.400 !important",
          opacity: 0.75,
        },
      }}
    />
  );
};
ChipForPoorEval.propTypes = {
  label: PropTypes.string,
  score: PropTypes.string,
  totalScore: PropTypes.string,
};
const TestDetailPoorEvaluations = ({ data }) => {
  return (
    <Box sx={{ marginX: 2 }}>
      <Accordion
        defaultExpanded
        disableGutters
        sx={{
          border: "1px solid",
          borderColor: "divider",
          borderRadius: "4px !important",
          overflow: "hidden",
          "&:before": { display: "none" },
          "&.Mui-expanded": {
            margin: 0,
          },
        }}
      >
        <AccordionSummary
          expandIcon={
            <Iconify
              icon="line-md:chevron-up"
              width={22}
              height={22}
              color="text.primary"
            />
          }
          sx={{
            px: 2,
            py: 1.5,
            backgroundColor: "background.default",
            "&:hover": {
              backgroundColor: "background.default",
            },
            "&.Mui-expanded": {
              backgroundColor: "background.default",
              minHeight: "unset",
            },
            "& .MuiAccordionSummary-content": {
              margin: 0,
            },
            "& .MuiAccordionSummary-content.Mui-expanded": {
              margin: 0,
            },
          }}
        >
          <Box display={"flex"} flexDirection={"column"}>
            <Typography
              variant="m3"
              fontWeight="fontWeightMedium"
              color="text.primary"
            >
              Poor performance evals
            </Typography>
          </Box>
        </AccordionSummary>

        <AccordionDetails
          sx={{
            px: 2,
            py: 0,
            pb: 2,
            backgroundColor: "background.default",
          }}
        >
          <Box display="flex" flexDirection="row" flexWrap="wrap" gap={2}>
            {data.map((e) => (
              <ChipForPoorEval key={e?.id} label={e?.name} />
            ))}
          </Box>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};
TestDetailPoorEvaluations.propTypes = {
  data: PropTypes.object,
};

export default TestDetailPoorEvaluations;
