import React from "react";
import { Helmet } from "react-helmet-async";
import WorkbenchView from "src/sections/workbench/WorkbenchView";

const Workbench = () => {
  return (
    <>
      <Helmet>
        <title>Prompt</title>
      </Helmet>
      <WorkbenchView />
    </>
  );
};

export default Workbench;
