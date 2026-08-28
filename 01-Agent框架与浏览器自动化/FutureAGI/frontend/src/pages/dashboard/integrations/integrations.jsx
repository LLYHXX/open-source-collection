import React from "react";
import { Helmet } from "react-helmet-async";
import { ProductDetailsView } from "src/sections/model/view";

// ----------------------------------------------------------------------

export default function IntegrationsPage() {
  return (
    <>
      <Helmet>
        <title> Dashboard: Connect Data</title>
      </Helmet>

      <ProductDetailsView />
    </>
  );
}
