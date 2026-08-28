import React from "react";
import { Helmet } from "react-helmet-async";
import ProjectDetailView from "src/sections/project-detail/ProjectDetailView";

const ProjectDetail = () => {
  return (
    <>
      <Helmet>
        <title>Prototype Detail</title>
      </Helmet>
      <ProjectDetailView />
    </>
  );
};

export default ProjectDetail;
