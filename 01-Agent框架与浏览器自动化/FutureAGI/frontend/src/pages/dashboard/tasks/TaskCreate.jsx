import React from "react";
import { Box } from "@mui/material";
import { Helmet } from "react-helmet-async";
import TaskCreatePage from "src/sections/tasks/TaskCreatePage";

const TaskCreate = () => {
  return (
    <>
      <Helmet>
        <title>Create Task</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: "background.paper",
          height: "100%",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <TaskCreatePage />
      </Box>
    </>
  );
};

export default TaskCreate;
