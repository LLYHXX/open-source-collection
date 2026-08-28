import { Box, Skeleton } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";
import { ShowComponent } from "src/components/show";

const AnnotationFieldSkeleton = ({ hideButtons }) => {
  return (
    <Box
      sx={{ display: "flex", gap: 1, alignItems: "center", paddingY: "10px" }}
    >
      <Skeleton sx={{ height: "50px", flex: 1, borderRadius: "12px" }} />
      <ShowComponent condition={!hideButtons}>
        <Skeleton sx={{ width: "28px", height: "28px" }} />
        <Skeleton sx={{ width: "28px", height: "28px" }} />
      </ShowComponent>
    </Box>
  );
};

AnnotationFieldSkeleton.propTypes = {
  hideButtons: PropTypes.bool,
};

export default AnnotationFieldSkeleton;
