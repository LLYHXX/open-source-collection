import React from "react";
import { Helmet } from "react-helmet-async";
import EvalsTasksViewV2 from "src/sections/common/EvalsTasks/EvalsTasksViewV2";

const TasksPage = () => {
  return (
    <>
      <Helmet>
        <title>Tasks</title>
      </Helmet>
      <EvalsTasksViewV2 />
    </>
  );
};

export default TasksPage;
