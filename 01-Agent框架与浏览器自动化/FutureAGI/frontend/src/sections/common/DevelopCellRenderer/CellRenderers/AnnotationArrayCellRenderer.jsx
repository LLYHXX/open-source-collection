import React from "react";
import PropTypes from "prop-types";
import { Skeleton } from "@mui/material";
import AnnotationCellRenderer from "../AnnotationCellRenderer/AnnotationCellRenderer";

const AnnotationArrayCellRenderer = ({ cellData, value }) => {
  if (
    cellData?.feedback_info?.annotation?.auto_annotate === true &&
    value === undefined
  ) {
    return (
      <Skeleton sx={{ width: "100%", height: "20px" }} variant="rounded" />
    );
  }

  return <AnnotationCellRenderer value={value} annotationData={cellData} />;
};

AnnotationArrayCellRenderer.propTypes = {
  cellData: PropTypes.object,
  value: PropTypes.any,
};

export default React.memo(AnnotationArrayCellRenderer);
