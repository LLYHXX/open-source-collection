import React, { useMemo } from "react";
import { useParams } from "react-router";
import PropTypes from "prop-types";
import { useQuery } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import EmptyCard from "../EmptyCard";
import { useRunEvaluationStoreShallow } from "../../states";
import EvalsCardGraphs from "./EvalsCardGraphs";

const EvalsCard = ({
  setCurrentTab,
  datasetId = null,
  selectedColumns,
  datasetIndex,
  selectedEvals = [],
}) => {
  const { dataset } = useParams();
  const setOpenRunEvaluation = useRunEvaluationStoreShallow(
    (s) => s.setOpenRunEvaluation,
  );

  const activeDatasetId = datasetId || dataset;

  const { data, isPending, isLoading } = useQuery({
    queryKey: ["evals-summary", activeDatasetId, selectedColumns],
    queryFn: () =>
      axios.get(endpoints.dataset.evalsSummary(activeDatasetId), {
        ...(selectedColumns?.length > 0 && {
          params: { column_ids: selectedColumns.join(",") },
        }),
      }),
    select: (e) => e?.data?.result || [],
    enabled: Boolean(activeDatasetId),
  });

  const formattedData = useMemo(() => {
    return selectedEvals?.length > 0
      ? data?.map((e) => ({
          ...e,
          isVisible: selectedEvals.includes(e?.id),
        }))
      : data?.map((e) => ({ ...e, isVisible: true }));
  }, [data, selectedEvals]);

  return (
    <EvalsCardGraphs
      emptyComponent={
        <EmptyCard
          tab={"evaluations"}
          setCurrentTab={setCurrentTab}
          action={() => setOpenRunEvaluation(true)}
          datasetId={datasetId}
          icon="/assets/icons/summary/empty-evals.svg"
          title="No evaluations added"
          description="To see the summary and evaluate your dataset, add evals to the dataset"
        />
      }
      data={formattedData}
      isPending={isPending}
      isLoading={isLoading}
      datasetIndex={datasetIndex}
    />
  );
};

EvalsCard.propTypes = {
  setCurrentTab: PropTypes.func,
  datasetId: PropTypes.string,
  selectedColumns: PropTypes.array,
  datasetIndex: PropTypes.number,
  selectedEvals: PropTypes?.array,
};

export default EvalsCard;
