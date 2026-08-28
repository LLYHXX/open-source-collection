import React from "react";
import { Helmet } from "react-helmet-async";
import WidgetEditorView from "src/sections/dashboards/WidgetEditorView";

export default function WidgetEditorPage() {
  return (
    <>
      <Helmet>
        <title>Widget Editor</title>
      </Helmet>
      <WidgetEditorView />
    </>
  );
}
