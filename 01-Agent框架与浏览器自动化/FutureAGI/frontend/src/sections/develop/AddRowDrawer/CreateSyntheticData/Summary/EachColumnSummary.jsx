import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Divider,
  Stack,
  Typography,
} from "@mui/material";
import PropTypes from "prop-types";
import React, { useState } from "react";
import Iconify from "src/components/iconify";

const titleProps = {
  variant: "s1",
  fontWeight: "fontWeightRegular",
  color: "text.primary",
};
const valueProps = {
  variant: "s1",
  fontWeight: "fontWeightMedium",
  color: "text.primary",
};

const EachColumnSummary = ({ data, index }) => {
  const [expanded, setExpanded] = useState(true);

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded((pre) => !pre)}
      sx={{
        border: "1px solid",
        borderColor: "divider",
        margin: "0px !important",
        backgroundColor: "background.neutral",
      }}
    >
      <AccordionSummary
        expandIcon={
          <Iconify
            // @ts-ignore
            icon="ooui:expand"
            width="16px"
            height="16px"
            color="text.primary"
          />
        }
        sx={{
          backgroundColor: "background.neutral",
          borderRadius: "8px",
          position: "relative",
          minHeight: "20px !important",
          "& .Mui-expanded": {
            m: "16px 16px 12px 0px",
          },
          "& .MuiAccordionSummary-expandIconWrapper": {
            marginRight: "10px",
          },
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <Typography
            fontWeight={"fontWeightSemiBold"}
            color="text.primary"
            // @ts-ignore
            variant="s1"
            sx={{ alignItems: "center" }}
          >
            Column {index + 1}:
          </Typography>
          <Typography
            color="text.primary"
            // @ts-ignore
            variant="s1"
            fontWeight="fontWeightRegular"
          >
            {data?.name}
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails
        sx={{
          marginTop: 0,
          paddingTop: 0,
          backgroundColor: "background.neutral",
          borderRadius: "0 0 8px 8px",
        }}
      >
        <Box
          sx={{
            backgroundColor: "background.paper",
            border: "1px solid",
            borderColor: "divider",
            borderRadius: "4px",
            display: "flex",
            flexDirection: "column",
            gap: "4px",
            padding: " 16px 12px",
          }}
        >
          <Box sx={{ width: "100%", display: "flex" }}>
            {/* @ts-ignore */}
            <Typography {...titleProps} sx={{ width: "50%" }} component="div">
              Column type:
            </Typography>
            {/* @ts-ignore */}
            <Typography {...valueProps} sx={{ width: "50%" }} component="div">
              {data?.data_type}
            </Typography>
          </Box>
          {data?.property
            ?.filter((item) => item.type && item.value && !item.category)
            ?.map((item, ind) => {
              const columnKey =
                item.type === "min_length"
                  ? "Min length"
                  : item.type === "max_length"
                    ? "Max length"
                    : item.type;
              return (
                <Box key={ind} sx={{ width: "100%", display: "flex" }}>
                  {/* @ts-ignore */}
                  <Typography
                    {...titleProps}
                    sx={{ width: "50%" }}
                    component="div"
                  >
                    {columnKey}
                  </Typography>
                  {/* @ts-ignore */}
                  <Typography
                    {...valueProps}
                    sx={{ width: "50%" }}
                    component="div"
                  >
                    {item.value}
                  </Typography>
                </Box>
              );
            })}

          {data?.description && (
            <>
              <Divider
                sx={{
                  my: 1.5,
                }}
              />
              <Stack gap={0.5}>
                <Typography {...titleProps}>Description: </Typography>
                <Typography {...valueProps}>{data?.description}</Typography>
              </Stack>
            </>
          )}
        </Box>
      </AccordionDetails>
    </Accordion>
  );
};

export default EachColumnSummary;

EachColumnSummary.propTypes = {
  data: PropTypes.object,
  index: PropTypes.number,
};
