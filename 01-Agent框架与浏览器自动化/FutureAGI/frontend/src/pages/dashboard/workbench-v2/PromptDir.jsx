import React from "react";
import { Helmet } from "react-helmet-async";
import PromptDirView from "../../../sections/workbench-v2/PromptDirView";

export default function PromptDir() {
  return (
    <>
      <Helmet>
        <title>Prompt</title>
      </Helmet>
      <PromptDirView />
    </>
  );
}
