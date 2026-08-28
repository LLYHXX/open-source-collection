import React from "react";
import { Box } from "@mui/material";
import { Helmet } from "react-helmet-async";
import EvalCreatePage from "src/sections/evals/components/EvalCreatePage";

const EvalCreate = () => {
  return (
    <>
      <Helmet>
        <title>Create Evaluation</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: "background.paper",
          height: "100%",
          p: 2,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <EvalCreatePage />
      </Box>
    </>
  );
};

export default EvalCreate;
