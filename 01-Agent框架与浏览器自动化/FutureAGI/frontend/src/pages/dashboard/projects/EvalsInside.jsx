import React from "react";
import { Helmet } from "react-helmet-async";
import { useParams } from "react-router";
import EvalsTasksViewV2 from "src/sections/common/EvalsTasks/EvalsTasksViewV2";

const EvalsInside = () => {
  const { observeId } = useParams();

  return (
    <>
      <Helmet>
        <title>Observe - Evals & Tasks</title>
      </Helmet>
      <EvalsTasksViewV2 observeId={observeId} />
    </>
  );
};

export default EvalsInside;
