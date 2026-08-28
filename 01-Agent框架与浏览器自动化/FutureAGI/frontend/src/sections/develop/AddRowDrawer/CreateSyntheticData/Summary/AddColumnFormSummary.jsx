// @ts-nocheck
import { Box } from "@mui/material";
import React from "react";
import { useFormContext } from "react-hook-form";
import EachColumnSummary from "./EachColumnSummary";

const AddColumnFormSummary = () => {
  const { getValues } = useFormContext();
  const { columns } = getValues();

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}
    >
      {columns?.map((item, index) => {
        return <EachColumnSummary key={index} data={item} index={index} />;
      })}
    </Box>
  );
};

export default AddColumnFormSummary;
