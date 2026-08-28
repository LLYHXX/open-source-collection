import React from "react";
import { Helmet } from "react-helmet-async";
import CreateSyntheticDataView from "src/sections/develop/AddRowDrawer/CreateSyntheticDataView";

const CreateSyntheticData = () => {
  return (
    <>
      <Helmet>
        <title>Create Synthetic Data</title>
      </Helmet>
      <CreateSyntheticDataView />
    </>
  );
};

export default CreateSyntheticData;
