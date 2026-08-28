import React from "react";
import { Helmet } from "react-helmet-async";
import SyncView from "src/sections/sync/SyncView";

const SyncData = () => {
  return (
    <>
      <Helmet>
        <title>Sync Data</title>
      </Helmet>
      <SyncView />
    </>
  );
};

export default SyncData;
