import React from "react";
import { Helmet } from "react-helmet-async";
import CallDetails from "src/sections/test-detail/CallDetails";

const TestExecutionCallDetail = () => {
  return (
    <>
      <Helmet>
        <title>Call Details</title>
      </Helmet>
      <CallDetails />
    </>
  );
};

export default TestExecutionCallDetail;
