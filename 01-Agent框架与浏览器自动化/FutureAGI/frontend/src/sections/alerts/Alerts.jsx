import React, { useEffect } from "react";
import { Helmet } from "react-helmet-async";
import AlertsView from "../projects/Alerts/AlertsView";
import {
  resetAlertStoreState,
  useAlertStore,
} from "../projects/Alerts/store/useAlertStore";
import { resetAlertSheetStoreState } from "../projects/Alerts/store/useAlertSheetStore";
import { resetAlertFilterStoreState } from "../projects/Alerts/store/useAlertFilterStore";
import { resetAlertSheetFilterStoreState } from "../projects/Alerts/store/useAlertSheetFilterStore";

export default function Alerts() {
  const { initializeWithMainPage } = useAlertStore();

  useEffect(() => {
    if (initializeWithMainPage) {
      initializeWithMainPage(true);
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
        <title>Alerts</title>
      </Helmet>
      <AlertsView />
    </>
  );
}
