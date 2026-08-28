import React from "react";
import { Helmet } from "react-helmet-async";
import ObserveListView from "src/sections/project/ObserveListView";

const ObserveList = () => {
  return (
    <>
      <Helmet>
        <title>Project - Observe</title>
      </Helmet>
      <ObserveListView />
    </>
  );
};

export default ObserveList;
