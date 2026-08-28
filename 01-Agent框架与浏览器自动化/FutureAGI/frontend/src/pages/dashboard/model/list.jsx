import React from "react";
import { Helmet } from "react-helmet-async";

import { ModelListView } from "src/sections/model/view";

// ----------------------------------------------------------------------

export default function ModelListPage() {
  return (
    <>
      <Helmet>
        <title> Dashboard: Product List</title>
      </Helmet>

      <ModelListView />
    </>
  );
}
