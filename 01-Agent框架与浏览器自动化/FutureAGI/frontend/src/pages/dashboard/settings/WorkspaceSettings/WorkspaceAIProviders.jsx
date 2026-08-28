import React from "react";
import { Helmet } from "react-helmet-async";
import AIProviders from "src/pages/dashboard/settings/AIProviders";

export default function WorkspaceAIProviders() {
  return (
    <>
      <Helmet>
        <title>Workspace AI Providers</title>
      </Helmet>
      <AIProviders />
    </>
  );
}
