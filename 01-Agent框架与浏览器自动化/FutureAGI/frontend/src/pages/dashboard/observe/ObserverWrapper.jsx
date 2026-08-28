import React from "react";
import { Helmet } from "react-helmet-async";
import ObserveView from "src/sections/projects/ObserveView";
import ObserveHeaderProvider from "src/sections/project/context/ObserveHeaderContextProvider";

const ObserverWrapper = () => {
  return (
    <>
      <Helmet>
        <title>Observe</title>
      </Helmet>
      <ObserveHeaderProvider>
        <ObserveView />
      </ObserveHeaderProvider>
    </>
  );
};

export default ObserverWrapper;
