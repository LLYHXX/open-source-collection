import React from "react";
import { Helmet } from "react-helmet-async";
import SessionExplorerSection from "src/sections/gateway/sessions/SessionExplorerSection";

const GatewaySessions = () => (
  <>
    <Helmet>
      <title>Gateway Sessions | Future AGI</title>
    </Helmet>
    <SessionExplorerSection />
  </>
);

export default GatewaySessions;
