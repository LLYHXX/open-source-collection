import React from "react";
import { Helmet } from "react-helmet-async";
import DataConnectView from "src/sections/data/view/data-connect-view";

// ----------------------------------------------------------------------

export default function ConnectDataPage() {
  return (
    <>
      <Helmet>
        <title> Dashboard: Connect Data</title>
      </Helmet>

      <DataConnectView />
    </>
  );
}
