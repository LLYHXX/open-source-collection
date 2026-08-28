import React from "react";
import { Helmet } from "react-helmet-async";
import { ProductDetailsView } from "src/sections/model/view";

// ----------------------------------------------------------------------

export default function ModelDetailsPage() {
  return (
    <>
      <Helmet>
        <title> Dashboard: Model Details</title>
      </Helmet>

      <ProductDetailsView />
    </>
  );
}
