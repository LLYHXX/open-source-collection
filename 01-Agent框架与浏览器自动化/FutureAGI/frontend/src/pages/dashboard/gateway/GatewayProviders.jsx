import React from "react";
import { Helmet } from "react-helmet-async";
import ProviderManagementSection from "src/sections/gateway/providers/ProviderManagementSection";

const GatewayProviders = () => (
  <>
    <Helmet>
      <title>Gateway Providers | Future AGI</title>
    </Helmet>
    <ProviderManagementSection />
  </>
);

export default GatewayProviders;
