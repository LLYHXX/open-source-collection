import React, { useEffect } from "react";
import { Helmet } from "react-helmet-async";
import AlertsView from "./AlertsView";
import { resetAlertStoreState, useAlertStore } from "./store/useAlertStore";
import { resetAlertSheetStoreState } from "./store/useAlertSheetStore";
import { resetAlertFilterStoreState } from "./store/useAlertFilterStore";
import { resetAlertSheetFilterStoreState } from "./store/useAlertSheetFilterStore";

export default function Alerts() {
  const { initializeWithMainPage } = useAlertStore();

  useEffect(() => {
    if (initializeWithMainPage) {
      initializeWithMainPage(false);
    }
    return () => {
      resetAlertSheetStoreState();
      resetAlertStoreState();
      resetAlertSheetFilterStoreState();
      resetAlertFilterStoreState();
    };
  }, [initializeWithMainPage]);
  return (
    <>
      <Helmet>
        <title>Observe - Alerts</title>
      </Helmet>
      <AlertsView />
    </>
  );
}
