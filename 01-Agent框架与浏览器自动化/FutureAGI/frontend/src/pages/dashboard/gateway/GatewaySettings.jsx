import React from "react";
import { Helmet } from "react-helmet-async";
import GatewaySettingsSection from "src/sections/gateway/settings/GatewaySettingsSection";

const GatewaySettings = () => (
  <>
    <Helmet>
      <title>Gateway Settings | Future AGI</title>
    </Helmet>
    <GatewaySettingsSection />
  </>
);

export default GatewaySettings;
