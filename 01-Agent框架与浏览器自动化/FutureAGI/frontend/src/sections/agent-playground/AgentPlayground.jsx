import React from "react";
import { Helmet } from "react-helmet-async";
import AgentPlaygroundView from "./AgentPlaygroundView";

export default function AgentPlayground() {
  return (
    <>
      <Helmet>
        <title>Playground</title>
      </Helmet>
      <AgentPlaygroundView />
    </>
  );
}
