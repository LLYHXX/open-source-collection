import React from "react";
import { Helmet } from "react-helmet-async";
import TestDetailView from "src/sections/test/TestDetailView";

const RunTestDetail = () => {
  return (
    <>
      <Helmet>
        <title>Test Details</title>
      </Helmet>
      <TestDetailView />
    </>
  );
};

export default RunTestDetail;
