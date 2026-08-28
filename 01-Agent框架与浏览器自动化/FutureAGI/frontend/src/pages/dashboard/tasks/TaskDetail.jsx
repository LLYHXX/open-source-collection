import React from "react";
import { Box } from "@mui/material";
import { Helmet } from "react-helmet-async";
import TaskDetailPage from "src/sections/tasks/TaskDetailPage";

const TaskDetail = () => {
  return (
    <>
      <Helmet>
        <title>Task Detail</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: "background.paper",
          height: "100%",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <TaskDetailPage />
      </Box>
    </>
  );
};

export default TaskDetail;
