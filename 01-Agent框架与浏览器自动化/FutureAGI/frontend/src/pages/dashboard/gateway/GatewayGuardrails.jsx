import React from "react";
import { Helmet } from "react-helmet-async";
import GuardrailManagementSection from "src/sections/gateway/guardrails/GuardrailManagementSection";

const GatewayGuardrails = () => (
  <>
    <Helmet>
      <title>Gateway Guardrails | Future AGI</title>
    </Helmet>
    <GuardrailManagementSection />
  </>
);

export default GatewayGuardrails;
