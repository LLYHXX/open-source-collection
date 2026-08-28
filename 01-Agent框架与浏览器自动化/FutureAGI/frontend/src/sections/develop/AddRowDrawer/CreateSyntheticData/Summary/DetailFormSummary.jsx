// @ts-nocheck
import { Box, Divider, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { useFormContext } from "react-hook-form";

const titleProps = {
  variant: "s1",
  fontWeight: "fontWeightMedium",
  color: "text.primary",
};
const valueProps = {
  variant: "s1",
  fontWeight: "fontWeightRegular",
  color: "text.secondary",
};

const DetailFormSummary = ({ selectedKB }) => {
  const { getValues } = useFormContext();
  const { name, kb_id, pattern, rowNumber, useCase, description } = getValues();

  if (!name && !kb_id && !pattern && !rowNumber && !useCase && !description) {
    return <></>;
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        backgroundColor: "background.neutral",
        border: "1px solid",
        borderColor: "divider",
        padding: "16px",
        borderRadius: "8px",
      }}
    >
      {name && (
        <Box sx={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <Typography {...titleProps}>Name</Typography>
            <Typography {...valueProps}>{name}</Typography>
          </Box>
          <Divider orientation="horizontal" sx={{ borderColor: "divider" }} />
        </Box>
      )}
      {kb_id && (
        <Box sx={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <Typography {...titleProps}>Knowledge base</Typography>
            <Typography {...valueProps}>{selectedKB}</Typography>
          </Box>
          <Divider orientation="horizontal" sx={{ borderColor: "divider" }} />
        </Box>
      )}
      {description && (
        <Box sx={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <Typography {...titleProps}>Description</Typography>
            <Typography {...valueProps}>{description}</Typography>
          </Box>
          <Divider orientation="horizontal" sx={{ borderColor: "divider" }} />
        </Box>
      )}
      {useCase && (
        <Box sx={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <Typography {...titleProps}>Objective</Typography>
            <Typography {...valueProps}>{useCase}</Typography>
          </Box>
          <Divider orientation="horizontal" sx={{ borderColor: "divider" }} />
        </Box>
      )}
      {pattern && (
        <Box sx={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <Typography {...titleProps}>Pattern</Typography>
            <Typography {...valueProps}>{pattern}</Typography>
          </Box>
          <Divider orientation="horizontal" sx={{ borderColor: "divider" }} />
        </Box>
      )}
      {rowNumber && (
        <Box sx={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <Typography {...titleProps}>No. of rows</Typography>
          <Typography {...valueProps}>{rowNumber}</Typography>
        </Box>
      )}
    </Box>
  );
};

export default DetailFormSummary;

DetailFormSummary.propTypes = {
  selectedKB: PropTypes.string,
};
