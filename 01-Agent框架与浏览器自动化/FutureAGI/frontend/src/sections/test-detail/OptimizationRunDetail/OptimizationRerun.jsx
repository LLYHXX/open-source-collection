import React from "react";
import RerunOptimizationModal from "../CreateEditOptimization/RerunOptimizationModal";
import { useOptimizationRunDetailStoreShallow } from "./states";
import { useTestDetail } from "../context/TestDetailContext";

const OptimizationRerun = () => {
  const { openOptimizationRerun, setOpenOptimizationRerun } =
    useOptimizationRunDetailStoreShallow((state) => ({
      openOptimizationRerun: state.openOptimizationRerun,
      setOpenOptimizationRerun: state.setOpenOptimizationRerun,
    }));

  const { refreshOptimizationGrid } = useTestDetail();
  return (
    <RerunOptimizationModal
      open={openOptimizationRerun}
      onClose={() => setOpenOptimizationRerun(null)}
      defaultValues={openOptimizationRerun}
      onSuccess={() => {
        refreshOptimizationGrid();
      }}
    />
  );
};

export default OptimizationRerun;
