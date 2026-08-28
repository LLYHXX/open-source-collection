import React from "react";
import { Helmet } from "react-helmet-async";
import WebhookManagementSection from "src/sections/gateway/webhooks/WebhookManagementSection";

const GatewayWebhooks = () => (
  <>
    <Helmet>
      <title>Gateway Webhooks | Future AGI</title>
    </Helmet>
    <WebhookManagementSection />
  </>
);

export default GatewayWebhooks;
