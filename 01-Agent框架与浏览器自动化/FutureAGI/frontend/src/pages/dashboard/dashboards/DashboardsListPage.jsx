import React from "react";
import { Helmet } from "react-helmet-async";
import DashboardsListView from "src/sections/dashboards/DashboardsListView";

export default function DashboardsListPage() {
  return (
    <>
      <Helmet>
        <title>Dashboards</title>
      </Helmet>
      <DashboardsListView />
    </>
  );
}
