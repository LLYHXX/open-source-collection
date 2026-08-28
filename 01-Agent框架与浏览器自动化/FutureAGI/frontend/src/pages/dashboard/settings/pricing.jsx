import React from "react";
import { Helmet } from "react-helmet-async";
import PricingPage from "src/sections/settings/PricingV3/PricingPage";

const Pricing = () => (
  <>
    <Helmet>
      <title>Plans & Pricing</title>
    </Helmet>
    <PricingPage />
  </>
);

export default Pricing;
