import React from "react";
import { Box } from "@mui/material";
import { Helmet } from "react-helmet-async";
import EvalDetailPage from "src/sections/evals/components/EvalDetailPage";

const EvalDetail = () => {
  return (
    <>
      <Helmet>
        <title>Evaluation Detail</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: "background.paper",
          height: "100%",
          p: 2,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <EvalDetailPage />
      </Box>
    </>
  );
};

export default EvalDetail;
