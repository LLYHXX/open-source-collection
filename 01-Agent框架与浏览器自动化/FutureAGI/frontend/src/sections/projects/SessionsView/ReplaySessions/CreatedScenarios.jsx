import React, { lazy, Suspense, useRef } from "react";
import GeneratedScenarios from "./GeneratedScenarios";
import AddedEvaluations from "./AddedEvaluations";
import { Box, Stack } from "@mui/material";
import { useReplaySessionsStoreShallow } from "./store";
import { ShowComponent } from "src/components/show";
import PropTypes from "prop-types";
import LoadingStages from "../../../../components/LoadingStages/LoadingStages";
const GraphPreview = lazy(
  () => import("src/sections/scenarios/scenario-detail/GraphPreview"),
);
import { CREATE_SCENARIO_STEPS } from "../../ReplayDrawer/common";
import { SCENARIO_STATUS } from "../../../../pages/dashboard/scenarios/common";
import { useFormContext } from "react-hook-form";

const CreatedScenarios = ({ scenarioDetail }) => {
  // keep track of the last scenario id to determine if the loading stages should be circular
  const lastScenarioId = useRef(scenarioDetail?.id);
  const { expandView } = useReplaySessionsStoreShallow((s) => ({
    expandView: s.expandView,
  }));
  const { watch } = useFormContext();
  const watchedProjectEvals = watch("projectEvals");
  const randomInitialStep = useRef(
    Math.floor(Math.random() * CREATE_SCENARIO_STEPS.length),
  );

  if (
    !scenarioDetail?.status ||
    scenarioDetail?.status === SCENARIO_STATUS.PROCESSING
  ) {
    const canUseCircular =
      lastScenarioId.current !== undefined &&
      scenarioDetail?.id !== undefined &&
      lastScenarioId.current === scenarioDetail.id;

    return (
      <LoadingStages
        style={{
          minHeight: "65vh",
        }}
        steps={CREATE_SCENARIO_STEPS}
        {...(canUseCircular
          ? {
              circularFromStart: true,
              initialStep: randomInitialStep.current,
            }
          : {})}
      />
    );
  }

  return (
    <Stack gap={2}>
      <GeneratedScenarios scenarioDetail={scenarioDetail} />
      <Stack direction={"row"} gap={2.5}>
        <ShowComponent condition={expandView}>
          <Box
            sx={{
              width: "100%",
              "& > div": { height: "320px", width: "100%" },
            }}
          >
            <Suspense fallback={null}>
              <GraphPreview scenario={scenarioDetail} viewOnly />
            </Suspense>
          </Box>
        </ShowComponent>
        <AddedEvaluations
          evaluationsAdded={watchedProjectEvals}
          // onAddMore={() => setOpenEvaluationDialog(true)}
          // setEvaluationsAdded={setEvaluationsAdded}
        />
      </Stack>
    </Stack>
  );
};

export default React.memo(CreatedScenarios);
CreatedScenarios.displayName = "CreatedScenarios";
CreatedScenarios.propTypes = {
  scenarioDetail: PropTypes.object.isRequired,
};
