import React, { useEffect } from "react";
import { Helmet } from "react-helmet-async";
import DevelopDetailView from "src/sections/develop-detail/DevelopDetailView";
import DevelopDetailProvider from "./Context/DevelopDetailProvider";
import { resetAllStates } from "src/sections/develop-detail/states";
import { resetEditSyntheticStates } from "src/sections/develop/AddRowDrawer/EditSyntheticData/state";

const DevelopDetail = () => {
  useEffect(() => {
    return () => {
      // delete compare file when component un mounts
      resetAllStates();
      resetEditSyntheticStates();
    };
  }, []);
  return (
    <>
      <Helmet>
        <title>Dataset Detail</title>
      </Helmet>
      <DevelopDetailProvider>
        <DevelopDetailView />
      </DevelopDetailProvider>
    </>
  );
};

export default DevelopDetail;
