import React from "react";
import { Helmet } from "react-helmet-async";
import KeyManagementSection from "src/sections/gateway/keys/KeyManagementSection";

const GatewayKeys = () => (
  <>
    <Helmet>
      <title>Gateway Keys | Future AGI</title>
    </Helmet>
    <KeyManagementSection />
  </>
);

export default GatewayKeys;
