import React from "react";
import { Helmet } from "react-helmet-async";
import CustomPropertySection from "src/sections/gateway/custom-properties/CustomPropertySection";

const GatewayCustomProperties = () => (
  <>
    <Helmet>
      <title>Gateway Custom Properties | Future AGI</title>
    </Helmet>
    <CustomPropertySection />
  </>
);

export default GatewayCustomProperties;
