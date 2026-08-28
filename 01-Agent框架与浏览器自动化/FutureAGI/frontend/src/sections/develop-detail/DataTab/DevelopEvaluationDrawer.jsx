import React from "react";
import EvaluationDrawer from "src/sections/common/EvaluationDrawer/EvaluationDrawer";
import { useRunEvaluationStore } from "../states";
import { useDatasetColumnConfig } from "src/api/develop/develop-detail";
import { useParams } from "react-router";
import { useDevelopDetailContext } from "../Context/DevelopDetailContext";

const DevelopEvaluationDrawer = () => {
  const { dataset } = useParams();

  const { openRunEvaluation, setOpenRunEvaluation } = useRunEvaluationStore();
  const allColumns = useDatasetColumnConfig(dataset);
  const { refreshGrid } = useDevelopDetailContext();
  return (
    <EvaluationDrawer
      open={openRunEvaluation}
      onClose={() => setOpenRunEvaluation(false)}
      onSuccess={(_data, _variables) => {
        // close drawer only when user wants to run evaluation directly
        if (_variables?.run) {
          setOpenRunEvaluation(false);
        }
      }}
      allColumns={allColumns?.filter((col) => col?.originType !== "evaluation")}
      refreshGrid={refreshGrid}
      type="temporary"
      module="dataset"
      id={dataset}
      showAdd
      showTest
      runLabel="Add & Run"
    />
  );
};

export default DevelopEvaluationDrawer;
