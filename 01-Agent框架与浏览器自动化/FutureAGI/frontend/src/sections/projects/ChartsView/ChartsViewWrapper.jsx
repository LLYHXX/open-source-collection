import React from "react";
import ChartsViewProvider from "./ChartsViewProvider/ChartsViewProvider";
import ChartsView from "./ChartsView";

export default function ChartsViewWrapper() {
  return (
    <ChartsViewProvider>
      <ChartsView />
    </ChartsViewProvider>
  );
}
