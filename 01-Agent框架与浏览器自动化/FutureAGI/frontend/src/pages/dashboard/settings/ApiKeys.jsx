import React from "react";
import { Helmet } from "react-helmet-async";
import ApiKeysLandingPage from "./api-keys/ApiKeysLandingPage";

export default function ApiKeys() {
  return (
    <>
      <Helmet>
        <title>API Keys</title>
      </Helmet>
      <ApiKeysLandingPage />
    </>
  );
}
