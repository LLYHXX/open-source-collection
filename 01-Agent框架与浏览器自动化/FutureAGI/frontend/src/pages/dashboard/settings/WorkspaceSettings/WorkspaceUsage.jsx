import React from "react";
import { Helmet } from "react-helmet-async";
import { useParams } from "react-router";
import UsageSummaryView from "src/sections/settings/UsageSummaryView/UsageSummaryView";

export default function WorkspaceUsage() {
  const { workspaceId } = useParams();
  return (
    <>
      <Helmet>
        <title>Workspace Usage</title>
      </Helmet>
      <UsageSummaryView workspaceId={workspaceId} />
    </>
  );
}
