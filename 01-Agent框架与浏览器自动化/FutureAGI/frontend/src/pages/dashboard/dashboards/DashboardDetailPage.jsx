import React from "react";
import { Helmet } from "react-helmet-async";
import DashboardDetailView from "src/sections/dashboards/DashboardDetailView";

export default function DashboardDetailPage() {
  return (
    <>
      <Helmet>
        <title>Dashboard</title>
      </Helmet>
      <DashboardDetailView />
    </>
  );
}
