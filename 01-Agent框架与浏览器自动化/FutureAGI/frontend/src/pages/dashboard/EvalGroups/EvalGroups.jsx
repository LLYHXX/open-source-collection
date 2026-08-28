import React from "react";
import { Helmet } from "react-helmet-async";
import Groups from "src/sections/evals/Groups/Groups.jsx";

export default function EvalGroups() {
  return (
    <>
      <Helmet>
        <title>Evaluations Groups</title>
      </Helmet>
      <Groups />
    </>
  );
}
